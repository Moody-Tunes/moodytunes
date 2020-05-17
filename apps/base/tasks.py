from logging import getLogger

from celery.schedules import crontab
from celery.task import PeriodicTask, Task
from django.conf import settings
from django.core.management import call_command

from libs.moody_logging import auto_fingerprint, update_logging_data


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
    run_every = crontab(minute=0, hour=3, day_of_week=0)

    """Task to backup mission critical database tables"""
    @update_logging_data
    def run(self, *args, **kwargs):
        logger.info(
            'Starting run to backup mission critical database tables',
            extra={'fingerprint': auto_fingerprint('start_database_backup', **kwargs)}
        )

        for model in settings.DATABASE_BACKUP_TARGETS:
            backup_filename = '{backup_directory}/{model_name}.json'.format(
                backup_directory=settings.DATABASE_BACKUPS_PATH,
                model_name=model
            )

            logger.info('Writing backup of {} to file {}'.format(model, backup_filename))

            call_command('dumpdata', model, output=backup_filename)

        logger.info(
            'Finished run to backup mission critical database tables',
            extra={'fingerprint': auto_fingerprint('finished_database_backup', **kwargs)}
        )
