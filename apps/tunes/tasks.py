from logging import getLogger
import os

from celery.task import task
from django.core.management import call_command

logger = getLogger(__name__)


@task(bind=True, max_retries=3, default_retry_delay=60*15)
def create_songs_from_spotify_task(self):
    """Periodic task to create songs from Spotify"""
    logger.info('Calling command to create songs from Spotify')

    # Disable writing to standard output when running command
    # Everything that we write to stdout gets logged anyway
    try:
        with open(os.devnull, 'w') as dev_null:
            call_command('tunes_create_songs_from_spotify', stdout=dev_null, stderr=dev_null)

    except Exception as exc:
        logger.warning('Exception raised when creating songs from Spotify: {}'.format(exc))
        self.retry(exc=exc)
