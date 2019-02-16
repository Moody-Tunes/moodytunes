import logging
import os

from celery.task import task
from django.core.management import call_command

logger = logging.getLogger(__name__)


@task()
def create_songs_from_spotify_task():
    """Periodic task to create songs from Spotify"""
    logger.info('Calling command to create songs from Spotify')

    # Disable writing to standard output when running command
    # Everything that we write to stdout gets logged anyway
    with open(os.devnull, 'w') as dev_null:
        call_command('tunes_create_songs_from_spotify', stdout=dev_null, stderr=dev_null)
