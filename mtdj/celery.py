import os

from celery import Celery
from celery.signals import setup_logging


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mtdj.settings')

app = Celery('mtdj')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@setup_logging.connect
def configure_logging(sender=None, **kwargs):
    """Configure celery logger to use the logging config defined in our settings file"""
    import logging.config
    from django.conf import settings

    logging.config.dictConfig(settings.LOGGING)
