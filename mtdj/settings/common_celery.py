from envparse import env

CELERY_TASK_ALWAYS_EAGER = env.bool('MTDJ_CELERY_TASK_ALWAYS_EAGER', default=False)
CELERY_BROKER_URL = env.str('MTDJ_CELERY_BROKER_URL', default='__broker_not_set__')
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'django-db'

# Define periodic tasks here as key:value pairs
# Key should be a string identifying the task to be run
# Value should be a dictionary containing configurations for the periodic task
#   - task: dotted.path.to.task
#   - schedule: Scheduler to use for calling task (crontab, seconds value, etc.)
CELERY_BEAT_SCHEDULE = {}