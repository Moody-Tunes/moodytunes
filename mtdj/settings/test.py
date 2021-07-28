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

DEFENDER_BEHIND_REVERSE_PROXY = False
DEFENDER_USE_CELERY = False

# We want to make it easy to create test users, so we'll remove the password
# validators when running tests
AUTH_PASSWORD_VALIDATORS = []

# Use a less secure password hashing algorithm to speed up test runs
PASSWORD_HASHERS = ['django.contrib.auth.hashers.UnsaltedMD5PasswordHasher']

CELERY_TASK_ALWAYS_EAGER = True

# Don't send emails when running unit tests
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

# Don't rely on django_compressor for unit tests
COMPRESS_ENABLED = False
COMPRESS_PRECOMPILERS = ()

# Use fake Spotify tokens during tests to ensure no requests to API are made
SPOTIFY.update({
    'client_id': 'test-spotify-client-id',
    'secret_key': 'test-spotify-secret_key',
})

# Configure SpotifyClient with authentication credentials
# Need to call this again to configure client to use test credentials
Config.configure(SPOTIFY['client_id'], SPOTIFY['client_id'])
