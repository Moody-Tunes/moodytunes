import logging

from celery.task import task
from django.core.management import call_command

logger = logging.getLogger(__name__)


@task()
def clear_expired_sessions():
    """Task to clean expired sessions from session storage"""
    logger.info('Calling django management command to clear expired sessions')

    try:
        call_command('clearsessions')
        logger.info('Successfully cleared expired sessions')
    except Exception:
        logger.exception('Caught exception when trying to clear expired sessions')
