from django.conf import settings
from django.urls import include, path

from base.views import HomePageView, LandingPageView


urlpatterns = [
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('moodytunes/', include(('moodytunes.urls', 'moodytunes'), namespace='moodytunes')),
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

    if 'rest_framework_swagger' in settings.INSTALLED_APPS:
        from rest_framework_swagger.views import get_swagger_view

        schema_view = get_swagger_view(title='API Docs', patterns=urlpatterns)

        urlpatterns = [
            path('docs/', schema_view, name='docs')
        ] + urlpatterns
