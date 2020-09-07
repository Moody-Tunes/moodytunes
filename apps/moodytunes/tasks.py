import logging
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from spotify_client import SpotifyClient
from spotify_client.exceptions import ClientException, SpotifyException

from accounts.models import SpotifyUserAuth
from base.tasks import MoodyBaseTask
from libs.moody_logging import auto_fingerprint, update_logging_data
from tunes.models import Song


logger = logging.getLogger(__name__)


class FetchSongFromSpotifyTask(MoodyBaseTask):
    default_retry_delay = 60 * 15
    autoretry_for = (SpotifyException,)

    @update_logging_data
    def run(self, spotify_code, username='anonymous', *args, **kwargs):
        """
        Use Spotify API to fetch song data for a given song and save the song to the database

        :param spotify_code: (str) Spotify URI for the song to be created
        :param username: (str) [Optional] Username for the user that requested this song
        """
        signature = 'tunes.tasks.FetchSongFromSpotifyTask-{}-{}'.format(username, spotify_code)

        # Early exit: if song already exists in our system don't do the work to fetch it
        if Song.objects.filter(code=spotify_code).exists():
            logger.info(
                'Song with code {} already exists in database'.format(spotify_code),
                extra={'fingerprint': auto_fingerprint('song_already_exists', **kwargs)}
            )
            return

        client = SpotifyClient(settings.SPOTIFY['client_id'], settings.SPOTIFY['secret_key'], identifier=signature)

        track_data = client.get_attributes_for_track(spotify_code)
        song_data = client.get_audio_features_for_tracks([track_data])[0]

        try:
            Song.objects.create(**song_data)

            logger.info(
                'Created song {} in database'.format(spotify_code),
                extra={
                    'fingerprint': auto_fingerprint('created_song', **kwargs),
                    'song_data': song_data,
                    'username': username,
                }
            )
        except ValidationError:
            logger.warning(
                'Failed to create song {}, already exists in database'.format(spotify_code),
                extra={'fingerprint': auto_fingerprint('failed_to_create_song', **kwargs)}
            )

            raise


class ExportSpotifyPlaylistFromSongsTask(MoodyBaseTask):
    default_retry_delay = 60 * 15
    autoretry_for = (SpotifyException,)

    @update_logging_data
    def get_or_create_playlist(self, auth_code, spotify_user_id, playlist_name, spotify, **kwargs):
        """
        Get the Spotify playlist by name for the user, creating it if it does not exist

        :param auth_code: (str) SpotifyUserAuth access_token for the given user
        :param spotify_user_id: (str) Spotify username for the given user
        :param playlist_name: (str) Name of the playlist to be created
        :param spotify: (spotify_client.SpotifyClient) Spotify Client instance

        :return: (str)
        """
        playlist_id = None

        try:
            resp = spotify.get_user_playlists(auth_code, spotify_user_id)
            playlists = resp['items']

            for playlist in playlists:
                if playlist['name'] == playlist_name:
                    playlist_id = playlist['id']
                    break

        except SpotifyException:
            logger.warning(
                'Error getting playlists for user {}'.format(spotify_user_id),
                exc_info=True,
                extra={
                    'fingerprint': auto_fingerprint('failed_getting_user_playlists', **kwargs),
                    'spotify_user_id': spotify_user_id,
                    'playlist_name': playlist_name,
                }
            )

        if playlist_id is None:
            playlist_id = spotify.create_playlist(auth_code, spotify_user_id, playlist_name)
            logger.info(
                'Created playlist for user {} with name {} successfully'.format(spotify_user_id, playlist_name),
                extra={'fingerprint': auto_fingerprint('created_spotify_playlist', **kwargs)}
            )

        return playlist_id

    def add_songs_to_playlist(self, auth_code, playlist_id, songs, spotify):
        """
        Call Spotify API to add songs to a playlist

        :param auth_code: (str) SpotifyUserAuth access_token for the given user
        :param playlist_id: (str) Spotify ID of the playlist to be created
        :param songs: (list) Collection of Spotify track URIs to add to playlist
        :param spotify: (spotify_client.SpotifyClient) Spotify Client instance

        """
        # Spotify has a limit of 100 songs per request to add songs to a playlist
        # Break up the total list of songs into batches of 100
        batched_songs = spotify.batch_tracks(songs)

        # First, remove songs from playlist to clear out already existing songs
        for batch in batched_songs:
            spotify.delete_songs_from_playlist(auth_code, playlist_id, batch)

        for batch in batched_songs:
            spotify.add_songs_to_playlist(auth_code, playlist_id, batch)

    @update_logging_data
    def upload_cover_image(self, auth_code, playlist_id, cover_image_filename, spotify, **kwargs):
        """
        Upload custom cover image for playlist. If any errors were encountered it will just fail
        silently.

        :param auth_code: (str) SpotifyUserAuth access_token for the given user
        :param playlist_id: (str) Spotify ID of the playlist to be created
        :param cover_image_filename: (str) Filename of cover image as a file on disk
        :param spotify: (spotify_client.SpotifyClient) Spotify Client instance
        """
        try:
            spotify.upload_image_to_playlist(auth_code, playlist_id, cover_image_filename)
        except (SpotifyException, ClientException):
            logger.warning(
                'Unable to upload cover image for playlist {}'.format(playlist_id),
                extra={'fingerprint': auto_fingerprint('failed_upload_cover_image', **kwargs)},
                exc_info=True
            )

    @update_logging_data
    def run(self, auth_id, playlist_name, songs, cover_image_filename=None, *args, **kwargs):
        auth = SpotifyUserAuth.get_and_refresh_spotify_user_auth_record(auth_id)

        # Check that user has granted proper scopes to export playlist to Spotify
        if not auth.has_scope(settings.SPOTIFY_PLAYLIST_MODIFY_SCOPE):
            logger.error(
                'User {} has not granted proper scopes to export playlist to Spotify'.format(auth.user.username),
                extra={
                    'fingerprint': auto_fingerprint('missing_scopes_for_playlist_export', **kwargs),
                    'auth_id': auth.pk,
                    'scopes': auth.scopes,
                }
            )

            raise Exception('Insufficient Spotify scopes to export playlist')

        spotify = SpotifyClient(
            settings.SPOTIFY['client_id'],
            settings.SPOTIFY['secret_key'],
            identifier='create_spotify_playlist_from_songs_{}'.format(auth.spotify_user_id)
        )

        logger.info(
            'Exporting songs to playlist {} for user {} on Spotify'.format(playlist_name, auth.spotify_user_id),
            extra={
                'fingerprint': auto_fingerprint('start_export_playlist', **kwargs),
                'auth_id': auth.pk
            }
        )

        playlist_id = self.get_or_create_playlist(auth.access_token, auth.spotify_user_id, playlist_name, spotify)

        # Upload cover image for playlist if specified
        if auth.has_scope(settings.SPOTIFY_UPLOAD_PLAYLIST_IMAGE) and cover_image_filename:
            self.upload_cover_image(auth.access_token, playlist_id, cover_image_filename, spotify)

        self.add_songs_to_playlist(auth.access_token, playlist_id, songs, spotify)

        # Delete cover image file from disk if present
        #
        # Do this after uploading songs to playlist to keep image file on disk
        # in case of errors with uploading songs to playlist to ensure that if
        # we need to retry because of errors with adding/deleting songs in playlist
        # that we still have the image file on disk for retries.
        if cover_image_filename:
            try:
                os.unlink(cover_image_filename)  # pragma: no cover
            except FileNotFoundError:
                pass

        logger.info(
            'Exported songs to playlist {} for user {} successfully'.format(playlist_name, auth.spotify_user_id),
            extra={
                'fingerprint': auto_fingerprint('success_export_playlist', **kwargs),
                'auth_id': auth.pk
            }
        )
