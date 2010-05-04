from datetime import datetime
from django.conf import settings
from django.db import models
from gearhump.users.models import Member
import hashlib

class DefaultPhoto(object):
  def thumb(self):
    return 'images/missing_thumb.jpg'

class GalleryManager(models.Manager):
  use_for_related_fields = True

  def recent(self):
    return self.with_extras().filter(active=True).order_by('-created')

  def top(self):
    return self.with_extras().filter(active=True).order_by('-favorite__count')

  def with_extras(self):
    return self.with_member().annotate(models.Count('comment')).annotate(
      models.Count('favorite'))

  def with_member(self):
    return self.select_related('member')


class Gallery(models.Model):
  name = models.CharField(max_length=128)
  description = models.TextField()
  member = models.ForeignKey(Member)
  created = models.DateTimeField(auto_now_add=True)
  upload_key = models.CharField(blank=True, max_length=32)
  active = models.BooleanField(default=False)
  favoritors = models.ManyToManyField(Member, through='Favorite',
                                      related_name='favorite_galleries')
  objects = GalleryManager()

  def photos(self, ids=None):
    qs = self.photo_set.filter(active=True)
    return qs.filter(id__in=ids) if ids else qs

  def comments(self):
    return self.comment_set.with_member().order_by('-created')

  def first_photo(self):
    try:
      return self.photo_set.filter(active=True)[0:1].get()
    except Photo.DoesNotExist:
      return DefaultPhoto()

  def prep_for_upload(self):
    self.upload_key = hashlib.md5(datetime.now().isoformat()).hexdigest()
    self.save()
    self.photo_set.filter(active=False).delete()
    return self.upload_key

  def finish_upload(self):
    self.upload_key = ''
    self.active = True
    self.save()
    self.photo_set.filter(active=False).update(active=True)

  def cancel_upload(self):
    self.upload_key = ''
    self.save()
    self.photo_set.filter(active=False).delete()

  def new_photo(self):
    return self.photo_set.create()

  def num_favorites(self):
    return self.favorite__count

  def num_comments(self):
    return self.comment__count

  def is_favorited(self, member):
    return self.favoritors.filter(id=member.id).exists()


class FavoriteManager(models.Manager):
  def add_favorite(self, member, gallery_id):
    self.create(gallery_id=gallery_id, member=member)

  def remove_favorite(self, member, gallery_id):
    self.filter(gallery=gallery_id, member=member).delete()


class Favorite(models.Model):
  gallery = models.ForeignKey(Gallery)
  member = models.ForeignKey(Member)
  date = models.DateTimeField(auto_now_add=True)
  objects = FavoriteManager()


class CommentManager(models.Manager):
  use_for_related_fields = True

  def with_member(self):
    return self.select_related('member')


class Comment(models.Model):
  gallery = models.ForeignKey(Gallery)
  member = models.ForeignKey(Member)
  created = models.DateTimeField(auto_now_add=True)
  body = models.TextField()
  objects = CommentManager()


class Photo(models.Model):
  gallery = models.ForeignKey(Gallery)
  active = models.BooleanField(default=False)

  def base(self):
    return 'user_images/' + str(self.id)

  def orig(self):
    return self.base() + '.jpg'

  def slide(self):
    return self.base() + '_s.jpg'

  def thumb(self):
    return self.base() + '_t.jpg'
