from django.urls import path

from moodytunes import views

urlpatterns = [
    path('browse/', views.BrowsePlaylistsView.as_view(), name='browse'),
    path('playlists/', views.EmotionPlaylistsView.as_view(), name='playlists')
]
