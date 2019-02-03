from django.urls import path

from moodytunes import views

urlpatterns = [
    path('browse/', views.BrowsePlaylistsView.as_view(), name='browse')
]