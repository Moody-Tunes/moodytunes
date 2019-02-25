from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

from base.views import HomePageView, PasswordResetDone


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('moodytunes/', include(('moodytunes.urls', 'moodytunes'), namespace='moodytunes')),
    path('tunes/', include(('tunes.urls', 'tunes'), namespace='tunes')),
    path('reset_password/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset_password_done/', PasswordResetDone.as_view(), name='password_reset_complete'),
    path('', HomePageView.as_view(), name='homepage')
]
