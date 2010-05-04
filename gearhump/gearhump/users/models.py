from django.contrib.auth.models import User
from django.db import models

class MemberManager(models.Manager):
  def create_from_user(self, user):
    return self.create(user=user, username=user.username)

class Member(models.Model):
  user = models.ForeignKey(User, unique=True)
  username = models.CharField(max_length=30)
  objects = MemberManager()

  def galleries(self):
    return self.gallery_set.with_extras().order_by('-created')

  def favorites(self):
    return self.favorite_galleries.with_extras().order_by('-favorite__date')

  def comments(self):
    return self.comment_set.order_by('-created')

  def galleries_preview(self):
    return self.galleries()[0:5]

  def favorites_preview(self):
    return self.favorites()[0:5]

  def comments_preview(self):
    return self.comments()[0:5]
