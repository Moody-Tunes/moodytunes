from django.urls import path

from spotify import views


urlpatterns = [
    path('authorize/', views.SpotifyAuthenticationView.as_view(), name='spotify-auth'),
    path('callback/', views.SpotifyAuthenticationCallbackView.as_view(), name='spotify-auth-callback'),
    path('success/', views.SpotifyAuthenticationSuccessView.as_view(), name='spotify-auth-success'),
    path('failure/', views.SpotifyAuthenticationFailureView.as_view(), name='spotify-auth-failure'),
    path('revoke/', views.RevokeSpotifyAuthView.as_view(), name='spotify-auth-revoke'),
    path('export/', views.ExportPlayListView.as_view(), name='export'),
    path('suggest/', views.SuggestSongView.as_view(), name='suggest'),
]
