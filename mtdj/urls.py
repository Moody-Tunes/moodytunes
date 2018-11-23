from django.contrib import admin
from django.urls import path, include

from base.views import HomePageView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('tunes/', include(('tunes.urls', 'tunes'), namespace='tunes')),
    path('', HomePageView.as_view(), name='homepage')
]
