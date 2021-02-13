from django.conf import settings
from django.urls import include, path

from base.views import HomePageView, LandingPageView


handler404 = 'base.views.not_found_handler'
handler500 = 'base.views.server_error_handler'


urlpatterns = [
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('moodytunes/', include(('moodytunes.urls', 'moodytunes'), namespace='moodytunes')),
    path('spotify/', include(('spotify.urls', 'spotify'), namespace='spotify')),
    path('tunes/', include(('tunes.urls', 'tunes'), namespace='tunes')),
    path('landing/', LandingPageView.as_view(), name='landing-page'),
    path('', HomePageView.as_view(), name='homepage')
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

    if 'drf_yasg' in settings.INSTALLED_APPS:
        from drf_yasg.views import get_schema_view
        from drf_yasg import openapi

        schema_view = get_schema_view(
            openapi.Info(title='MoodyTunes API', default_version='v1'),
            patterns=urlpatterns,
        )

        urlpatterns = [
            path('docs/', schema_view.with_ui('swagger'), name='docs')
        ] + urlpatterns
