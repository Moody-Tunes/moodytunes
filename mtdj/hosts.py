from django.conf import settings
from django_hosts import host, patterns


host_patterns = patterns(
    '',
    host(r'admin', 'mtdj.admin_urls', name='admin'),
    host(r'www', settings.ROOT_URLCONF, name='www')
)
