# Test specific settings

from .common import *

# Don't write to the console during unit test
LOGGING['root']['handlers'] = ['app_file', 'error_file']

# Disable caching when running unit tests
CACHES['default'] = CACHES['dummy']

# We want to make it easy to create test users, so we'll remove the password
# validators when running tests
AUTH_PASSWORD_VALIDATORS = []

CELERY_TASK_ALWAYS_EAGER = True

# Test encryption key
FIELD_ENCRYPTION_KEY = 'kNSxgnDzatFuh89K-NGamVPy3wvbTGjwR9V9al1bnZA='

# Don't send emails when running unit tests
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

# Don't rely on django_compressor for unit tests
COMPRESS_ENABLED = False
COMPRESS_PRECOMPILERS = ()

# Use sqlite3 database for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
