from logging import getLogger
import os

from celery.schedules import crontab

from django.core.management import call_command

from base.tasks import MoodyPeriodicTask

logger = getLogger(__name__)


class CreateSongsFromSpotifyTask(MoodyPeriodicTask):
    run_every = crontab(minute=0, hour=1, day_of_week=0)

    max_retries = 3
    default_retry_delay = 60 * 15

    def run(self, *args, **kwargs):
        """Periodic task to create songs from Spotify"""
        logger.info('Calling command to create songs from Spotify')

        # Disable writing to standard output when running command
        # Everything that we write to stdout gets logged anyway
        try:
            with open(os.devnull, 'w') as dev_null:
                return call_command('tunes_create_songs_from_spotify', stdout=dev_null, stderr=dev_null)

        except Exception as exc:
            logger.warning('Exception raised when creating songs from Spotify: {}'.format(exc))
            self.retry(exc=exc)
