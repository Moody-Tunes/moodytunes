from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('', RedirectView.as_view(pattern_name='accounts:login', permanent=True, query_string=True))
]
