from django.contrib.auth import views as auth_views
from django.urls import path

from accounts import views

urlpatterns = [
    # Authentication views
    path('login/', views.MoodyLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('reset_password/', views.MoodyPasswordResetView.as_view(), name='reset-password'),
    path(
        'reset_password/<uidb64>/<token>/',
        views.MoodyPasswordResetConfirmView.as_view(),
        name='password-reset-confirm'
    ),
    path('reset_password_done/', views.MoodyPasswordResetDone.as_view(), name='password-reset-complete'),

    # Moodytunes management
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('update/', views.UpdateInfoView.as_view(), name='update'),
    path('create/', views.CreateUserView.as_view(), name='create'),

    # Django Rest Framework endpoints
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
]
