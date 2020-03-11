from django.conf import settings
from django.urls import path, include

from base.views import HomePageView


urlpatterns = [
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('moodytunes/', include(('moodytunes.urls', 'moodytunes'), namespace='moodytunes')),
    path('tunes/', include(('tunes.urls', 'tunes'), namespace='tunes')),
    path('', HomePageView.as_view(), name='homepage')
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
