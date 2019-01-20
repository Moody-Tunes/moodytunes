from envparse import env
import os
import tempfile

from . import BASE_DIR
from .common_api import *

SECRET_KEY = env.str('DJANGO_SECRET_KEY', default='__insecure_installation__')

DEBUG = env.bool('DJANGO_DEBUG', default=False)

ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=[])

APPEND_SLASH = True

SITE_URL = env.str('MTDJ_SITE_URL', default='moodytunes.localhost')

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
    'django_extensions',
    'rest_framework',
]

OUR_APPS = [
    'accounts',
    'base',
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
SECURE_BROWSER_XSS_FILTER =  True

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

DATABASES = env.json('DJANGO_DATABASES', default={
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
})

CACHES = env.json('DJANGO_CACHES', default={
    'default': {
        'VERSION': 1,
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '{}/mtdj_cache'.format(tempfile.gettempdir()),
    }
})

CACHES.update({
    'dummy': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
})

AUTH_USER_MODEL = 'accounts.MoodyUser'
LOGIN_REDIRECT_URL = '/accounts/profile/'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
COUNTRY_CODE = env.str('MTDJ_COUNTRY_CODE', default='US')  # ISO 3166-1 alpha-2 code

TIME_ZONE = 'EST'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'

# Email settings
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
}

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
            'filename': env.str('DJANGO_LOG_APP_FILENAME', default=os.path.join(BASE_DIR, 'dev_app.log')),
            'formatter': 'json',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': env.str('DJANGO_LOG_ERROR_FILENAME', default=os.path.join(BASE_DIR, 'dev_err.log')),
            'formatter': 'json',
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
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
