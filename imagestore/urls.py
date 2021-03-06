# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf.urls import url
from django.urls import include, path
from .views import *
from . import views
app_name = 'imagestore'

urlpatterns = [
    url(r'^$', AlbumListView.as_view(), name='index'),

    url(r'^album/add/$', CreateAlbum.as_view(), name='create-album'),
    url(r'^album/add/(?P<album_id>\d+)/$', CreateAlbum.as_view(), name='add-subalbum-to-album'),
    url(r'^album/(?P<album_id>\d+)/$', ImageListView.as_view(), name='album'),
    url(r'^album/(?P<pk>\d+)/edit/$', UpdateAlbum.as_view(), name='update-album'),
    url(r'^album/(?P<pk>\d+)/delete/$', DeleteAlbum.as_view(), name='delete-album'),

    url(r'^tag/(?P<tag>[^/]+)/$', ImageListView.as_view(), name='tag'),

    url(r'^user/(?P<user_id>\w+)/albums/', AlbumListView.as_view(), name='user'),
    url(r'^user/(?P<user_id>\w+)/$', ImageListView.as_view(), name='user-images'),

    url(r'^upload/album/(?P<album_id>\d+)/$', CreateImage.as_view(), name='upload-image-to-album'),

    url(r'^image/(?P<pk>\d+)/$', ImageView.as_view(), name='image'),
    url(r'^album/(?P<album_id>\d+)/image/(?P<pk>\d+)/$', ImageView.as_view(), name='image-album'),
    url(r'^image/(?P<pk>\d+)/delete/$', DeleteImage.as_view(), name='delete-image'),
    url(r'^image/(?P<pk>\d+)/update/$', UpdateImage.as_view(), name='update-image'),

    url(r'^tag-autocomplete/$', ImageTagAutocompleteView.as_view(), name='tag-autocomplete'),
    url(r'^sidebarsubalbums/$', views.sidebarsubalbums, name='sidebar_subalbums'),
]
