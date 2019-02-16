from celery.task import task
from celery.utils.log import get_task_logger
from django.core.management import call_command

logger = get_task_logger(__name__)


@task()
def clear_expired_sessions():
    """Task to clean expired sessions from session storage"""
    logger.info('Calling django management command to clear expired sessions')

    call_command('clearsessions')
