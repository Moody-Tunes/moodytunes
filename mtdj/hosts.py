from django.conf import settings
from django.contrib import admin
from django_hosts import patterns, host


host_patterns = patterns(
    '',
    host(r'admin', admin.site.urls, name='admin'),
    host(r'www', settings.ROOT_URLCONF, name='www')
)
