from logging import getLogger
import os

from celery.task import task
from django.core.management import call_command

from tunes.models import Song
from libs.spotify import SpotifyClient

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


@task(bind=True)
def update_song_danceabilty(self, song_id):
    """
    Update song record with danceability data from Spotify

    :param song_id: (int) Primary key for song in table
    """
    try:
        song = Song.objects.get(pk=song_id)
    except (Song.MultipleObjectsReturned, Song.DoesNotExist):
        logger.warning('Song with pk {} could not be retrieved'.format(song_id))
        raise

    logger.info('Fetching danceability value for song {}'.format(song.code))

    spotify_client = SpotifyClient(identifier='update_song_danceability_{}'.format(song.code))
    song_data = {'code': song.code}
    attributes = spotify_client.get_audio_features_for_tracks([song_data])
    danceability = attributes[0]['danceability']

    song.danceability = danceability
    song.save()

    logger.info('Successfully updated danceability for song {}'.format(song.code))
