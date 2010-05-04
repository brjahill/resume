from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.views import static
from os import path
import os
import traceback

def serve(request, key):
  if request.method == 'GET':
    return static.serve(request, key, settings.MEDIA_ROOT)
  elif request.method == 'PUT':
    try:
      file_path = path.join(settings.MEDIA_ROOT, key)
      dir_path = path.dirname(file_path)
      if not path.exists(dir_path):
        os.makedirs(dir_path)
      file = open(file_path, "w")
      file.write(request.raw_post_data)
      file.close()
      return HttpResponse()
    except:
      traceback.print_exc()
  else:
    raise Http404
