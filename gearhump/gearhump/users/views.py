from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.simple import direct_to_template
from gearhump.galleries.views import gallery_list
from gearhump.users.models import Member

def signup(request):
  form = UserCreationForm(request.POST or None)
  if form.is_valid():
    new_user = form.save()
    Member.objects.create_from_user(new_user)
    new_user = authenticate(username=new_user.username,
                            password=form.cleaned_data['password1'])
    login(request, new_user)
    return redirect(settings.LOGIN_REDIRECT_URL)
  return direct_to_template(request, 'registration/signup.html', locals())

def profile(request, username):
  member = get_object_or_404(Member, username=username)
  return direct_to_template(request, 'users/profile.html', locals())

def user_gallery_list(request, username):
  member = get_object_or_404(Member, username=username)
  return gallery_list(request, member.galleries(), username + "'s galleries",
                      show_poster=False)

def favorite_list(request, username):
  member = get_object_or_404(Member, username=username)
  return gallery_list(request, member.favorites(), username + "'s favorites")
