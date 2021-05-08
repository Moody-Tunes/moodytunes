from datetime import timedelta

from . import env


CELERY_TASK_ALWAYS_EAGER = env.bool('MTDJ_CELERY_TASK_ALWAYS_EAGER', default=False)
CELERY_BROKER_URL = env.str('MTDJ_CELERY_BROKER_URL', default='__broker_not_set__')
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_BEAT_SYNC_EVERY = 1
CELERY_RESULT_EXPIRES = timedelta(days=90)  # Delete result records after 90 days

DJANGO_CELERY_RESULTS = {
    'ALLOW_EDITS': False  # Disable editing results in admin interface
}
