from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_list
from functools import wraps
from gearhump.galleries import forms, models
from gearhump.galleries.photos import delete_photo_files
import hashlib
import json

# Helpers

def takes_gallery(check_owner=False):
  def inner_takes_gallery(view, owner=False):
    def _takes_gallery(request, gallery_id, *args, **kwargs):
      gallery = get_object_or_404(models.Gallery.objects.with_member(),
                                  id=gallery_id)
      if owner and gallery.member != request.user.get_profile():
        return redirect('galleries:detail', gallery.id)
      return view(request, gallery, *args, **kwargs)
    return wraps(view)(_takes_gallery)
  if callable(check_owner):
    return inner_takes_gallery(check_owner)
  return lambda func: inner_takes_gallery(func, check_owner)

def gallery_list(request, qs, title, show_poster=True):
  return object_list(request, queryset=qs,
                     paginate_by=settings.GALLERIES_PER_PAGE,
                     template_name='galleries/gallery_list.html',
                     extra_context=locals(), template_object_name='gallery')

# Views

@login_required
def new(request):
  form = forms.GalleryForm(request.POST or None)
  if form.is_valid():
    gallery = form.create(request.user.get_profile())
    return redirect('galleries:upload', gallery.id)
  return direct_to_template(request, 'galleries/gallery_form.html', locals())

@login_required
@takes_gallery(check_owner=True)
def edit(request, gallery):
  form = forms.GalleryForm(request.POST or None, instance=gallery)
  if form.is_valid():
    form.save()
    return redirect('galleries:detail', gallery.id)
  return direct_to_template(request, 'galleries/gallery_form.html', locals())

@login_required
@takes_gallery(check_owner=True)
def upload(request, gallery):
  upload_key = gallery.prep_for_upload()
  upload_url = settings.PHOTO_UPLOAD_URL
  return direct_to_template(request, 'galleries/upload.html', locals())

@takes_gallery
def new_photo(request, gallery, upload_key):
  if upload_key != gallery.upload_key:
    return HttpResponseBadRequest()
  photo = gallery.new_photo()
  response = json.dumps({'photo_id': photo.id})
  return HttpResponse(response, mimetype='application/json')

@login_required
@takes_gallery(check_owner=True)
def upload_success(request, gallery):
  gallery.finish_upload()
  return direct_to_template(request, 'galleries/upload_success.html', locals())

@login_required
@takes_gallery(check_owner=True)
def upload_failure(request, gallery):
  gallery.cancel_upload()
  return direct_to_template(request, 'galleries/upload_failure.html', locals())

@login_required
@takes_gallery(check_owner=True)
def delete_photos(request, gallery):
  form = forms.DeletePhotosForm(gallery.photos(), request.POST or None)
  if form.is_valid():
    form.hide()
    num_photos = len(form.cleaned_data['to_delete'])
    return direct_to_template(request, 'galleries/delete_photos_confirm.html',
                              locals())
  return direct_to_template(request, 'galleries/delete_photos.html', locals())

@login_required
@takes_gallery(check_owner=True)
def do_delete_photos(request, gallery):
  form = forms.DeletePhotosForm(gallery.photos(), request.POST or None)
  if not form.is_valid():
    return redirect('galleries:delete_photos', gallery.id)
  photos = gallery.photos(ids=form.deleted_ids())
  delete_photo_files(photos)
  photos.delete()
  return redirect('galleries:detail', gallery.id)

@login_required
@takes_gallery(check_owner=True)
def delete(request, gallery):
  if request.method == 'POST':
    delete_photo_files(gallery.photos())
    gallery.delete()
    return direct_to_template(request, 'galleries/delete_success.html')
  return direct_to_template(request, 'galleries/delete.html', locals())

@takes_gallery
def detail(request, gallery, photo_id=0):
  images = gallery.photos()
  if images:
    curr_img = images[0]
    for img in images:
      if img.id == int(photo_id):
        curr_img = img
  comment_form = forms.CommentForm(auto_id=False)
  if request.user.is_authenticated():
    favorited = gallery.is_favorited(request.user.get_profile())
    is_owner = request.user.get_profile() == gallery.member
  else:
    is_owner = False
  return direct_to_template(request, 'galleries/detail.html', locals())

@login_required
@takes_gallery
def new_comment(request, gallery):
  form = forms.CommentForm(request.POST)
  if form.is_valid():
    form.create(request.user.get_profile(), gallery)
  return redirect('galleries:detail', gallery.id)

@login_required
def delete_comment(request, gallery_id, comment_id):
  comment = get_object_or_404(models.Comment, id=comment_id)
  if request.user.get_profile() == comment.member:
    comment.delete()
  return redirect('galleries:detail', gallery_id)

@login_required
def favorite(request, gallery_id):
  models.Favorite.objects.add_favorite(request.user.get_profile(), gallery_id)
  return redirect('galleries:detail', gallery_id)

@login_required
def unfavorite(request, gallery_id):
  models.Favorite.objects.remove_favorite(request.user.get_profile(),
                                          gallery_id)
  return redirect('galleries:detail', gallery_id)

def recent(request):
  return gallery_list(request, models.Gallery.objects.recent(),
                      'Recent galleries')

def top(request):
  return gallery_list(request, models.Gallery.objects.top(),
                      'Top galleries')
