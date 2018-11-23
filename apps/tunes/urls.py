from django.urls import path

from tunes import views


urlpatterns = [
    path('browse/', views.BrowseView.as_view(), name='browse'),
]
