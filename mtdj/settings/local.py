# local development configuration
# If you would lke to override any settings, create a local_personal.py file
# that imports this module. Then you are free to override any settings values
# you would like
#
# settings/local_personal.py
# from .local import *
#
# SOME_VARIABLE_TO_OVERRIDE = 'my_value'
#
from .common import *

import tempfile


# We want to make it easy to create test users, so we'll remove the password
# validators locally
AUTH_PASSWORD_VALIDATORS = []

CELERY_TASK_ALWAYS_EAGER = True

# Add ability to log messages to console
LOGGING['handlers'].update({
    'console': {
        'level': 'DEBUG',
        'class': 'libs.moody_logging.StackInfoHandler',
        'formatter': 'simple',
    },
})

# Django debug toolbar configuration
INSTALLED_APPS.append('debug_toolbar')
MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

LOGGING['handlers']['app_file']['level'] = 'DEBUG'
LOGGING['root']['handlers'].append('console')
LOGGING['root']['level'] = 'DEBUG'
