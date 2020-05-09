from django.urls import path

from moodytunes import views


urlpatterns = [
    path('about/', views.AboutView.as_view(), name='about'),
    path('browse/', views.BrowsePlaylistsView.as_view(), name='browse'),
    path('playlists/', views.EmotionPlaylistsView.as_view(), name='playlists'),
    path('suggest/', views.SuggestSongView.as_view(), name='suggest'),
    path('export/', views.ExportPlayListView.as_view(), name='export'),
    path('spotify/authorize/', views.SpotifyAuthenticationView.as_view(), name='spotify-auth'),
    path('spotify/callback/', views.SpotifyAuthenticationCallbackView.as_view(), name='spotify-auth-callback'),
    path('spotify/success/', views.SpotifyAuthenticationSuccessView.as_view(), name='spotify-auth-success'),
    path('spotify/failure/', views.SpotifyAuthenticationFailureView.as_view(), name='spotify-auth-failure')
]
