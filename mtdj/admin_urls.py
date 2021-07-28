from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from accounts.views import MoodyLogoutView


urlpatterns = [
    path('logout/', MoodyLogoutView.as_view(), name='logout'),
    path(r'', admin.site.urls, name='admin'),
    path('admin/defender/', include('defender.urls')),
]

if settings.DEBUG:
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

    if 'silk' in settings.INSTALLED_APPS:
        import silk.urls

        urlpatterns = [
            path('silk/', include(silk.urls))
        ] + urlpatterns
