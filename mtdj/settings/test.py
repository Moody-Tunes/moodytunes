# Test specific settings

from .common import *

# Don't write to the console during unit test
LOGGING['root']['handlers'] = ['app_file', 'error_file']

# Disable caching when running unit tests
CACHES['default'] = CACHES['dummy']

# We want to make it easy to create test users, so we'll remove the password
# validators when running tests
AUTH_PASSWORD_VALIDATORS = []

CELERY_ALWAYS_EAGER = True

# Use sqlite3 database for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'test_db.sqlite3'),
    }
}
