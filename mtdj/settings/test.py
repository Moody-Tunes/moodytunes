# Test specific settings

import logging

from .common import *


# Disable logging
logging.disable(logging.CRITICAL)

# Disable caching when running unit tests
CACHES['default'] = CACHES['dummy']

# Set session store to use dummy cache for tests
SESSION_CACHE_ALIAS = 'default'

DATABASE_BACKUPS_PATH = tempfile.gettempdir()
IMAGE_FILE_UPLOAD_PATH = tempfile.gettempdir()

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

# Use fake Spotify tokens during tests to ensure no requests to API are made
SPOTIFY.update({
    'client_id': 'test-spotify-client-id',
    'secret_key': 'test-spotify-secret_key',
    'auth_redirect_uri': 'https://moodytunes.vm/moodytunes/spotify/callback/'
})
