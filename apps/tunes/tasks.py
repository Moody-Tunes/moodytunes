import os
from logging import getLogger

from celery.schedules import crontab
from django.core.management import CommandError, call_command

from base.tasks import MoodyPeriodicTask


logger = getLogger(__name__)


class CreateSongsFromSpotifyTask(MoodyPeriodicTask):
    run_every = crontab(minute=0, hour=1, day_of_week=0)

    default_retry_delay = 60 * 15
    autoretry_for = (CommandError,)

    def run(self, *args, **kwargs):
        """Periodic task to create songs from Spotify"""
        logger.info('Calling command to create songs from Spotify')

        # Disable writing to standard output when running command
        # Everything that we write to stdout gets logged anyway
        with open(os.devnull, 'w') as dev_null:
            return call_command('tunes_create_songs_from_spotify', stdout=dev_null, stderr=dev_null)
