import os
import tempfile

from envparse import env

from . import BASE_DIR
from .common_api import *
from .common_celery import *


SECRET_KEY = env.str('DJANGO_SECRET_KEY', default='')

DEBUG = env.bool('DJANGO_DEBUG', default=False)

SITE_HOSTNAME = env.str('MTDJ_SITE_HOSTNAME', default='moodytunes.localhost')
INTERNAL_IPS = ('127.0.0.1',)
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=[SITE_HOSTNAME, 'admin.{}'.format(SITE_HOSTNAME)])

# Admins are defined in cradle with the `name, email;` pattern
ADMINS = []
admin_config = env.str('DJANGO_ADMINS', default='')

if admin_config:
    admins = admin_config.split(';')

    for admin in admins:
        name, email = admin.split(',')
        ADMINS.append((name.strip(), email.strip()))

APPEND_SLASH = True

WEBMASTER_EMAIL = env.str('MTDJ_WEBMASTER_EMAIL', default='foo@example.com')

# App definitions
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'compressor',
    'django_extensions',
    'django_celery_beat',
    'django_celery_results',
    'dbbackup',
    'django_hosts',
    'easy_timezones',
    'encrypted_model_fields',
    'rest_framework',
    'waffle',
]

OUR_APPS = [
    'accounts',
    'base',
    'moodytunes',
    'tunes',
]

INSTALLED_APPS = DJANGO_APPS + OUR_APPS + THIRD_PARTY_APPS

MIDDLEWARE = [
    'django_hosts.middleware.HostsRequestMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'easy_timezones.middleware.EasyTimezoneMiddleware',
    'waffle.middleware.WaffleMiddleware',
    'django_hosts.middleware.HostsResponseMiddleware',
]

# Security middleware definitions
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Enable HSTS header for site
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_PRELOAD = True  # Include site in HSTS preload list
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = True  # Add `secure` flag when setting session cookie
SESSION_COOKIE_HTTPONLY = True  # Add `HttpOnly` flag when setting session cookie

CSRF_COOKIE_SECURE = True  # Add `secure` flag when setting CSRF cookie
CSRF_COOKIE_HTTPONLY = True  # Add `HttpOnly` flag when setting CSRF cookie

ROOT_URLCONF = 'mtdj.urls'
ROOT_HOSTCONF = 'mtdj.hosts'
DEFAULT_HOST = 'www'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mtdj.wsgi.application'

FIELD_ENCRYPTION_KEY = env.str('MTDJ_ENCRYPTED_FIELDS_KEY', default='__encrypted-field-key-not-set__')

DATABASES = {
    'default': {
        'ENGINE': env.str('MTDJ_DATABASE_ENGINE', default='django.db.backends.postgresql'),
        'NAME': env.str('MTDJ_DATABASE_NAME', default='mtdj_local_database'),
        'USER': env.str('MTDJ_DATABASE_USER', default=''),
        'PASSWORD': env.str('MTDJ_DATABASE_PASSWORD', default='__database-password-not-set__'),
        'HOST': env.str('MTDJ_DATABASE_HOST', default='127.0.0.1'),
        'PORT': env.str('MTDJ_DATABASE_PORT', default='5432')
    }
}

# django-dbbackup options
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {
    'location': env.str('MTDJ_DATABASE_BACKUPS_PATH', default='/tmp')
}


CACHES = {
    'default': {
        'VERSION': env.int('MTDJ_CACHE_VERSION', default=1),
        'BACKEND': env.str('MTDJ_CACHE_BACKEND', default='django.core.cache.backends.filebased.FileBasedCache'),
        'LOCATION': env.str('MTDJ_CACHE_LOCATION', default='{}/mtdj_cache'.format(tempfile.gettempdir())),
        'OPTIONS': {
            'CLIENT_CLASS': env.str('MTDJ_CACHE_CLIENT', default=''),
        },
        'KEY_PREFIX': 'mtdj'
    },
    'dummy': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

GENRE_CHOICES_CACHE_KEY = 'song-genre-choices'

BROWSE_PLAYLIST_CACHE_TIMEOUT = 60 * 10  # 10 minutes
GENRE_CHOICES_CACHE_TIMEOUT = 60 * 60 * 24 * 7  # 1 week

AUTH_USER_MODEL = 'accounts.MoodyUser'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/accounts/profile/'
LOGOUT_REDIRECT_URL = '/accounts/logout/'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 9}},
]

LANGUAGE_CODE = 'en-us'
COUNTRY_CODE = env.str('MTDJ_COUNTRY_CODE', default='US')  # ISO 3166-1 alpha-2 code

TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, '_static')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'compressor.finders.CompressorFinder',
)

# Always compress static files with django_compressor
COMPRESS_ENABLED = True
UGLIFY_BINARY = env.str('MTDJ_UGLIFY_BINARY', default='node_modules/uglify-es/bin/uglifyjs')
UGLIFY_ARGUMENTS = env.str('MTDJ_UGLIFY_OPTIONS', default='-m')

"""
NOTE: COMPRESS_OFFLINE determines whether static files should be checked and recompiled as part of the
request/response cycle. We DO NOT want to do this in prod, for two reasons:
    1. We compile static files during deployment, so any files that were changed are recompiled
    2. We DO NOT want the gunicorn process to be writing to the _static directory
Essentially, we want the production application to just use whatever files are in the cache (use the offline compressed
files.) We do want development to compress on the fly, so that engineers don't need to recompile every time they make
a change to static files.
"""
COMPRESS_OFFLINE = env.bool('MTDJ_COMPRESS_OFFLINE', default=False)

COMPRESS_PRECOMPILERS = (
   ('text/less', 'node_modules/less/bin/lessc {infile} {outfile}'),
)

COMPRESS_JS_FILTERS = (
    'libs.compressors.UglifyJSFilter',
)

# Email settings
SYSTEM_EMAIL_ADDRESS = env.str('MTDJ_SYSTEM_EMAIL_ADDRESS', default='ops@moodytunes.us')
DEFAULT_FROM_EMAIL = SYSTEM_EMAIL_ADDRESS

EMAIL_BACKEND = env.str('DJANGO_EMAIL_BACKEND', default='django.core.mail.backends.filebased.EmailBackend')
EMAIL_FILE_PATH = '{}/django_emails/'.format(tempfile.gettempdir())  # For file-based email backend
EMAIL_HOST = env.str('DJANGO_EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('DJANGO_EMAIL_PORT', default=25)
EMAIL_HOST_USER = env.str('DJANGO_EMAIL_USER', default='')
EMAIL_HOST_PASSWORD = env.str('DJANGO_EMAIL_PASSWORD', default='')
EMAIL_USE_TLS = env.bool('DJANGO_EMAIL_USE_TLS', default=True)

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.UserRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'user': '5/sec',
    },
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    )
}

LOGGING_DIR = env.str('DJANGO_APP_LOG_DIR', default=BASE_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname}|{asctime}|{pathname}@{lineno}|{name} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'fmt': '%(levelname)s %(asctime)s %s(pathname)s %(lineno)s %(name)s %(message)s',
        },
        'simple': {
            'format': '{levelname}: {name} - {message}',
            'style': '{',
        },
        'gunicorn': {
            'format': '{message}',
            'style': '{'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'app_file': {
            'level': 'INFO',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': '{}/application.log'.format(LOGGING_DIR),
            'formatter': 'json',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': '{}/error.log'.format(LOGGING_DIR),
            'formatter': 'json',
        },
        'gunicorn': {
            'level': 'INFO',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': '{}/gunicorn.log'.format(LOGGING_DIR),
            'formatter': 'gunicorn',
        },
        'celery': {
            'level': 'INFO',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': '{}/celery.log'.format(LOGGING_DIR),
            'formatter': 'json',
        },
        'database': {
            'level': 'DEBUG',
            'class': 'libs.moody_logging.StackInfoHandler',
            'filename': '{}/database.log'.format(LOGGING_DIR)
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'gunicorn': {
            'handlers': ['gunicorn'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['celery'],
            'level': 'INFO',
            'propagate': False,
        },
        'django_celery_beat': {
            'handlers': ['celery'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['mail_admins', 'app_file', 'error_file'],
        'level': 'INFO',
        'propagate': False,
    },
}

# GeoIP Database files
GEOIP2_DATABASE = os.path.join(BASE_DIR, 'GeoLiteCity.mmdb')

# Strategies for generating browse playlist
BROWSE_PLAYLIST_STRATEGIES = ['energy', 'valence', 'danceability']
