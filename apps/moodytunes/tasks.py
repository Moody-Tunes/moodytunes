import logging

from celery.task import task

from tunes.models import Song
from libs.spotify import SpotifyClient, SpotifyException


logger = logging.getLogger(__name__)


@task(bind=True, max_retries=3, default_retry_delay=60*15)
def fetch_song_from_spotify(self, spotify_code):
    """
    Use Spotify API to fetch song data for a given song and save the song to the database

    :param spotify_code: (str) Spotify URI for the song to be created
    """
    signature = 'fetch_song_from_spotify'
    client = SpotifyClient(identifier=signature)
    song_data = None

    try:
        logger.info('{} - Making request to Spotify for song data for {}'.format(signature, spotify_code))
        track_data = client.get_attributes_for_track(spotify_code)
        song_data = client.get_audio_features_for_tracks([track_data])[0]
    except SpotifyException:
        logger.warning('{} - Failed to fetch song from Spotify. Retrying'.format(signature))
        self.retry()

    if song_data:
        Song.objects.get_or_create(code=song_data['code'], defaults=song_data)
        logger.info('{} - Created song {} in database'.format(signature, spotify_code))
    else:
        logger.info('{} - Could not create song {} in database. Retrying'.format(signature, spotify_code))
        self.retry()
