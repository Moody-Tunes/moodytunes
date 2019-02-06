CELERY_TASK_ALWAYS_EAGER = True
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/1'
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
