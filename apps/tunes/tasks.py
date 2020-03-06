from logging import getLogger
import os

from celery.task import task
from django.core.management import call_command

from libs.spotify import SpotifyClient, SpotifyException

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


@task(bind=True, max_retries=3, default_retry_delay=60*15)
def create_spotify_playlist_from_songs(self, auth_code, spotify_user_id, playlist_name, songs):
    """
    Create a playlist on a user's Spotify account from a list of tracks in our system.

    :param auth_code: (str) SpotifyUserAuth access_token for the given user
    :param spotify_user_id: (str) Spotify username for the given user
    :param playlist_name: (str) Name of the playlist to be created
    :param songs: (list) Collection of Spotify track URIs to add to playlist

    """
    spotify = SpotifyClient()

    try:
        logger.info('Creating playlist for user {}'.format(spotify_user_id))
        playlist_id = spotify.create_playlist(auth_code, spotify_user_id, playlist_name)
        logger.info('Created playlist for user {} successfully'.format(spotify_user_id))
    except SpotifyException:
        logger.warning('Error creating playlist for user {}, retrying...'.format(spotify_user_id))
        self.retry()

    try:
        logger.info('Adding songs to playlist {}'.format(playlist_id))
        spotify.add_songs_to_playlist(auth_code, playlist_id, songs)
        logger.info('Added songs to playlist {} successfully'.format(playlist_id))
    except SpotifyException:
        logger.warning('Error adding songs to playlist {} for user {}, retrying...'.format(
            playlist_id,
            spotify_user_id
        ))
        self.retry()
        