from django.urls import path

from tunes import views


urlpatterns = [
    path('browse/', views.BrowseView.as_view(), name='browse'),
    path('vote/', views.VoteView.as_view(), name='vote'),
    path('playlist/', views.PlaylistView.as_view(), name='playlist'),
    path('options/', views.OptionView.as_view(), name='options'),
    path('last/', views.LastPlaylistView.as_view(), name='last')
]
