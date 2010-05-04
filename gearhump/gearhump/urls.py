from django.conf import settings
from django.conf.urls.defaults import *
import gearhump.galleries.urls
import gearhump.users.urls

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
                       (r'', include(gearhump.users.urls.include)),
                       (r'', include(gearhump.galleries.urls.include)),
                      )

if settings.FAKE_S3:
    urlpatterns += patterns('gearhump.fakes3.views',
                            url(r'^fakes3/(.*)$', 'serve'))
