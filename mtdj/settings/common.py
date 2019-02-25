from envparse import env
import os
import tempfile

from . import BASE_DIR
from .common_api import *
from .common_celery import *

SECRET_KEY = env.str('DJANGO_SECRET_KEY', default='__insecure_installation__')

DEBUG = env.bool('DJANGO_DEBUG', default=False)

SITE_HOSTNAME = env.str('MTDJ_SITE_HOSTNAME', default='moodytunes.localhost')
INTERNAL_IPS = ('127.0.0.1',)
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=[SITE_HOSTNAME])

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
    'rest_framework',
]

OUR_APPS = [
    'accounts',
    'base',
    'moodytunes',
    'tunes',
]

INSTALLED_APPS = DJANGO_APPS + OUR_APPS + THIRD_PARTY_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Security middleware definitions
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = True  # Add `secure` flag when setting session cookie
SESSION_COOKIE_HTTPONLY = True  # Add `HttpOnly` flag when setting session cookie

CSRF_COOKIE_SECURE = True  # Add `secure` flag when setting CSRF cookie

ROOT_URLCONF = 'mtdj.urls'

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

CACHES = {
    'default': {
        'VERSION': env.int('MTDJ_CACHE_VERSION', default=1),
        'BACKEND': env.str('MTDJ_CACHE_BACKEND', default='django.core.cache.backends.filebased.FileBasedCache'),
        'LOCATION': env.str('MTDJ_CACHE_LOCATION', default='{}/mtdj_cache'.format(tempfile.gettempdir())),
        'OPTIONS': {
            'CLIENT_CLASS': env.str('MTDJ_CACHE_CLIENT', default=''),
        },
        'KEY_PREFIX': 'mtdj'
    }}

CACHES.update({
    'dummy': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
})

AUTH_USER_MODEL = 'accounts.MoodyUser'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/accounts/profile/'
LOGOUT_REDIRECT_URL = LOGIN_URL

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 9}},
]

LANGUAGE_CODE = 'en-us'
COUNTRY_CODE = env.str('MTDJ_COUNTRY_CODE', default='US')  # ISO 3166-1 alpha-2 code

TIME_ZONE = 'EST'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = '_static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'compressor.finders.CompressorFinder',
)

# Always compress static files with django_compressor
COMPRESS_ENABLED = True

COMPRESS_PRECOMPILERS = (
   ('text/less', 'lessc {infile} {outfile}'),
)

# Email settings
EMAIL_BACKEND = env.str('DJANGO_EMAIL_BACKEND', default='django.core.mail.backends.filebased.EmailBackend')
EMAIL_FILE_PATH = env.str('DJANGO_EMAIL_FILE_PATH', default='{}/django_emails/'.format(tempfile.gettempdir()))
SYSTEM_EMAIL_ADDRESS = env.str('MTDJ_SYSTEM_EMAIL_ADDRESS', default='ops@moodytunes.us')

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
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['mail_admins', 'app_file', 'error_file'],
        'level': 'INFO',
        'propagate': False,
    },
}
