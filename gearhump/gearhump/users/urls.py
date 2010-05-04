from django.conf import settings
from django.conf.urls.defaults import *

urls = patterns('django.contrib.auth.views',
                url(r'^login/?$', 'login', name='login'),
                url(r'^logout/?$', 'logout',
                    {'next_page': settings.LOGIN_REDIRECT_URL}, name='logout'),
               )

urls += patterns('gearhump.users.views',
                 url(r'^signup/?$', 'signup', name='signup'),
                 url(r'^users/(\w+)/?$', 'profile', name='profile'),
                 url(r'^users/(\w+)/galleries/?$', 'user_gallery_list',
                     name='gallery_list'),
                 url(r'^users/(\w+)/favorites/?$', 'favorite_list',
                     name='favorite_list'),
                )

include = (urls, 'users', 'users')
