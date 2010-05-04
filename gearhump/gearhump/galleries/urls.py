from django.conf import settings
from django.conf.urls.defaults import *

urls = patterns('gearhump.galleries.views',
                url(r'^$', 'recent', name='home'),
                url(r'^g/new/?$', 'new', name='new'),
                url(r'^g/(\d+)/edit/?$', 'edit', name='edit'),
                url(r'^g/(\d+)/upload/?$', 'upload', name='upload'),
                url(r'^g/(\d+)/new_photo/(\w+)/?$', 'new_photo',
                    name='new_photo'),
                url(r'^g/(\d+)/upload_success/?$', 'upload_success',
                    name='upload_success'),
                url(r'^g/(\d+)/upload_failure/?$', 'upload_failure',
                    name='upload_failure'),
                url(r'^g/(\d+)/delete_photos/?$', 'delete_photos',
                    name='delete_photos'),
                url(r'^g/(\d+)/do_delete_photos/?$', 'do_delete_photos',
                    name='do_delete_photos'),
                url(r'^g/(\d+)/delete/?$', 'delete', name='delete'),
                url(r'^g/(\d+)/?$', 'detail', name='detail'),
                url(r'^g/(\d+)/photos/(\d+)/?$', 'detail',
                    name='detail_photo'),
                url(r'^g/(\d+)/new_comment/?$', 'new_comment',
                    name='new_comment'),
                url(r'^g/(\d+)/delete_comment/(\d+)/?$', 'delete_comment',
                    name='delete_comment'),
                url(r'^g/(\d+)/favorite/?$', 'favorite', name='favorite'),
                url(r'^g/(\d+)/unfavorite/?$', 'unfavorite',
                    name='unfavorite'),
                url(r'^g/recent/?$', 'recent', name='recent'),
                url(r'^g/top/?$', 'top', name='top'),
               )

include = (urls, 'galleries', 'galleries')
