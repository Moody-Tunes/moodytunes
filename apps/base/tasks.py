from logging import getLogger

from celery.task import task
from django.core.management import call_command

logger = getLogger(__name__)


@task()
def clear_expired_sessions():
    """Task to clean expired sessions from session storage"""
    logger.info('Calling django management command to clear expired sessions')

    call_command('clearsessions')
