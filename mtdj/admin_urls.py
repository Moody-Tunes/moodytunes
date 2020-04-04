from django.conf import settings
from django.contrib import admin
from django.urls import path, include

from accounts.views import MoodyLogoutView


urlpatterns = [
    path('logout/', MoodyLogoutView.as_view(), name='logout'),
    path(r'', admin.site.urls, name='admin'),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
