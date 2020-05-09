from logging import getLogger

from celery.schedules import crontab
from celery.task import PeriodicTask, Task
from django.core.management import call_command


logger = getLogger(__name__)


class MoodyBaseTask(Task):
    abstract = True


class MoodyPeriodicTask(MoodyBaseTask, PeriodicTask):
    abstract = True
    run_every = None
    ignore_result = None


class ClearExpiredSessionsTask(MoodyPeriodicTask):
    run_every = crontab(minute=0, hour=2, day_of_week=0)

    """Task to clean expired sessions from session storage"""
    def run(self, *args, **kwargs):
        logger.info('Calling django management command to clear expired sessions')

        call_command('clearsessions')


class BackupDatabaseTask(MoodyPeriodicTask):
    run_every = crontab(minute=0, hour=1, day_of_week=0)

    """Task to make backups of application database"""
    def run(self, *args, **kwargs):
        logger.info('Calling django management command to backup database')

        call_command('dbbackup')
