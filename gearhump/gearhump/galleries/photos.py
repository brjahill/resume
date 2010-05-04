from boto.s3.connection import S3Connection
from django.conf import settings
import os

def delete_photo_files(photos):
  try:
    if not settings.FAKE_S3:
      conn = S3Connection(settings.AWS_ACCESS, settings.AWS_SECRET)
      bucket = conn.get_bucket(settings.S3_BUCKET)
      for photo in photos:
        if settings.FAKE_S3:
          os.remove(os.path.join(settings.MEDIA_ROOT, photo.orig()))
          os.remove(os.path.join(settings.MEDIA_ROOT, photo.slide()))
          os.remove(os.path.join(settings.MEDIA_ROOT, photo.thumb()))
        else:
          bucket.delete_key(photo.orig())
          bucket.delete_key(photo.slide())
          bucket.delete_key(photo.thumb())
  except:
    pass
