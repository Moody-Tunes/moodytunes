from logging import getLogger

from celery.schedules import crontab
from celery.task import Task, PeriodicTask
from django.core.management import call_command

logger = getLogger(__name__)


class MoodyBaseTask(Task):
    abstract = True


class MoodyPeriodicTask(MoodyBaseTask, PeriodicTask):
    abstract = True
    run_every = None


class ClearExpiredSessionsTask(MoodyPeriodicTask):
    name = 'base.tasks.ClearExpiredSessionsTask'
    run_every = crontab(minute=0, hour=2, day_of_week=0)

    """Task to clean expired sessions from session storage"""
    def run(self, *args, **kwargs):
        logger.info('Calling django management command to clear expired sessions')

        call_command('clearsessions')
