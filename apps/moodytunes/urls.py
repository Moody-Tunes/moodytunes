from django.urls import path

from moodytunes import views

urlpatterns = [
    path('about/', views.AboutView.as_view(), name='about'),
    path('browse/', views.BrowsePlaylistsView.as_view(), name='browse'),
    path('playlists/', views.EmotionPlaylistsView.as_view(), name='playlists')
]
