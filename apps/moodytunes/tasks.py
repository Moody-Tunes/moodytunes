import logging

from celery.task import task

from tunes.models import Song
from libs.spotify import SpotifyClient, SpotifyException


logger = logging.getLogger(__name__)


@task(bind=True, max_retries=3, default_retry_delay=60*15)
def fetch_song_from_spotify(self, spotify_code, username='anonymous'):
    """
    Use Spotify API to fetch song data for a given song and save the song to the database

    :param spotify_code: (str) Spotify URI for the song to be created
    :param username: (str) [Optional] Username for the user that requested this song
    """
    signature = 'fetch_song_from_spotify-{}-{}'.format(username, spotify_code)

    # Early exit: if song already exists in our system don't do the work to fetch it
    if Song.objects.filter(code=spotify_code).exists():
        logger.info('{} - Song with code {} already exists in database'.format(signature, spotify_code))
        return

    client = SpotifyClient(identifier=signature)
    song_data = None

    try:
        logger.info('{} - Making request to Spotify for song data for {}'.format(signature, spotify_code))
        track_data = client.get_attributes_for_track(spotify_code)
        song_data = client.get_audio_features_for_tracks([track_data])[0]
    except SpotifyException:
        logger.warning('{} - Failed to fetch song data from Spotify. Retrying'.format(signature), exc_info=True)
        self.retry()

    if song_data:
        # Decode track data name/artist from unicode to string
        song_data['name'] = song_data['name'].decode('utf-8')
        song_data['artist'] = song_data['artist'].decode('utf-8')
        _, created = Song.objects.get_or_create(code=song_data['code'], defaults=song_data)

        if created:
            logger.info('{} - Created song {} in database'.format(signature, spotify_code))
        else:
            logger.info('{} - Did not create song {} in database, song already exists'.format(signature, spotify_code))
