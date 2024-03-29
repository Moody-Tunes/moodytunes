import os
from logging import getLogger

from celery.schedules import crontab
from celery.task import PeriodicTask, Task
from django.conf import settings
from django.core.management import call_command

from libs.moody_logging import auto_fingerprint, update_logging_data


logger = getLogger(__name__)


class MoodyBaseTask(Task):
    abstract = True

    max_retries = 3
    autoretry_for = ()

    # Add autoretry behavior for a defined tuple of exceptions to retry on
    # From https://github.com/celery/celery/issues/4684#issuecomment-547861259
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.autoretry_for and not hasattr(self, '_orig_run'):
            def run(*args, **kwargs):
                try:
                    return self._orig_run(*args, **kwargs)
                except self.autoretry_for as exc:
                    self.retry(exc=exc)

            self._orig_run, self.run = self.run, run


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
    run_every = crontab(minute=0, hour=4, day_of_week=0)

    @update_logging_data
    def delete_old_backups(self, **kwargs):
        for backup_file in os.listdir(settings.DATABASE_BACKUPS_PATH):
            if any([backup_file.startswith(model) for model in settings.DATABASE_BACKUP_TARGETS]):
                backup_filename = os.path.join(settings.DATABASE_BACKUPS_PATH, backup_file)
                logger.info(
                    'Deleting old backup {}'.format(backup_filename),
                    extra={'fingerprint': auto_fingerprint('delete_old_backup', **kwargs)}
                )
                os.unlink(backup_filename)

    @update_logging_data
    def backup_models(self, **kwargs):
        for model in settings.DATABASE_BACKUP_TARGETS:
            backup_filename = '{backup_directory}/{model_name}.json'.format(
                backup_directory=settings.DATABASE_BACKUPS_PATH,
                model_name=model
            )

            logger.info(
                'Writing backup of {} to file {}'.format(model, backup_filename),
                extra={
                    'fingerprint': auto_fingerprint('backup_database_model', **kwargs),
                    'model': model,
                }
            )

            call_command('dumpdata', model, output=backup_filename)

    """Task to backup mission critical database tables"""
    @update_logging_data
    def run(self, *args, **kwargs):
        logger.info(
            'Starting run to backup mission critical database tables',
            extra={'fingerprint': auto_fingerprint('start_database_backup', **kwargs)}
        )

        self.delete_old_backups()
        self.backup_models()

        logger.info(
            'Finished run to backup mission critical database tables',
            extra={'fingerprint': auto_fingerprint('finished_database_backup', **kwargs)}
        )
