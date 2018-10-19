from django.contrib.auth import views as auth_views
from django.urls import path

from accounts import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='logout.html'), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('update/', views.UpdateInfoView.as_view(), name='update')
]
