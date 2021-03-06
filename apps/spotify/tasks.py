import logging
import os

from celery.schedules import crontab
from django.conf import settings
from django.core.exceptions import ValidationError
from spotify_client import SpotifyClient
from spotify_client.exceptions import ClientException, SpotifyException

from base.tasks import MoodyBaseTask, MoodyPeriodicTask
from libs.moody_logging import auto_fingerprint, update_logging_data
from spotify.exceptions import InsufficientSpotifyScopesError
from spotify.models import SpotifyAuth, SpotifyUserData
from tunes.models import Song


logger = logging.getLogger(__name__)


class UpdateTopArtistsFromSpotifyTask(MoodyBaseTask):
    default_retry_delay = 60 * 15
    autoretry_for = (SpotifyException,)

    @update_logging_data
    def run(self, auth_id, *args, **kwargs):
        trace_id = kwargs.get('trace_id', '')
        auth = SpotifyAuth.get_and_refresh_spotify_auth_record(auth_id, trace_id=trace_id)

        # Check that user has granted proper scopes to fetch top artists from Spotify
        if not auth.has_scope(settings.SPOTIFY_TOP_ARTIST_READ_SCOPE):
            logger.error(
                'User {} has not granted proper scopes to fetch top artists from Spotify'.format(auth.user.username),
                extra={
                    'fingerprint': auto_fingerprint('missing_scopes_for_update_top_artists', **kwargs),
                    'auth_id': auth.pk,
                    'scopes': auth.scopes,
                    'trace_id': trace_id,
                }
            )

            raise InsufficientSpotifyScopesError('Insufficient Spotify scopes to fetch Spotify top artists')

        spotify_client_identifier = 'update_spotify_top_artists_{}'.format(auth.spotify_user_id)
        spotify = SpotifyClient(identifier=spotify_client_identifier)

        logger.info(
            'Updating top artists for {}'.format(auth.spotify_user_id),
            extra={
                'fingerprint': auto_fingerprint('update_spotify_top_artists', **kwargs),
                'trace_id': trace_id,
            }
        )

        artists = spotify.get_user_top_artists(auth.access_token, settings.SPOTIFY['max_top_artists'])
        spotify_user_data, _ = SpotifyUserData.objects.get_or_create(spotify_auth=auth)
        spotify_user_data.top_artists = artists
        spotify_user_data.save()

        logger.info(
            'Successfully updated top artists for {}'.format(auth.spotify_user_id),
            extra={
                'fingerprint': auto_fingerprint('success_update_spotify_top_artists', **kwargs),
                'trace_id': trace_id,
            }
        )


class RefreshTopArtistsFromSpotifyTask(MoodyPeriodicTask):
    run_every = crontab(minute=0, hour=3, day_of_week=0)

    @update_logging_data
    def run(self, *args, **kwargs):
        auth_records = SpotifyAuth.objects.all()

        logger.info(
            'Starting run to refresh top artists for {} auth records'.format(auth_records.count()),
            extra={'fingerprint': auto_fingerprint('refresh_top_artists', **kwargs)}
        )

        for auth in auth_records:
            UpdateTopArtistsFromSpotifyTask().delay(auth.pk)


class ExportSpotifyPlaylistFromSongsTask(MoodyBaseTask):
    default_retry_delay = 60 * 15
    autoretry_for = (SpotifyException,)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trace_id = None

    @update_logging_data
    def get_or_create_playlist(self, auth_code, spotify_user_id, playlist_name, spotify, **kwargs):
        """
        Get the Spotify playlist by name for the user, creating it if it does not exist

        :param auth_code: (str) SpotifyAuth access_token for the given user
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
                    'trace_id': self.trace_id,
                }
            )

        if playlist_id is None:
            playlist_id = spotify.create_playlist(auth_code, spotify_user_id, playlist_name)
            logger.info(
                'Created playlist for user {} with name {} successfully'.format(spotify_user_id, playlist_name),
                extra={
                    'fingerprint': auto_fingerprint('created_spotify_playlist', **kwargs),
                    'trace_id': self.trace_id,
                }
            )

        return playlist_id

    def delete_all_songs_from_playlist(self, auth_code, playlist_id, spotify):
        """
        Delete all the songs from the given playlist, to ensure we end up with a
        playlist that only contains the songs to be added from the MoodyTunes
        playlist to be exported

        :param auth_code: (str) SpotifyAuth access_token for the given user
        :param playlist_id: (str) Spotify ID of the playlist to be created
        :param spotify: (spotify_client.SpotifyClient) Spotify Client instance
        """
        songs = spotify.get_all_songs_from_user_playlist(auth_code, playlist_id)

        # Early exit; if no songs are in the playlist then skip clearing the playlist
        if not songs:
            return

        batched_songs = spotify.batch_tracks(songs)

        for batch in batched_songs:
            spotify.delete_songs_from_playlist(auth_code, playlist_id, batch)

    def add_songs_to_playlist(self, auth_code, playlist_id, songs, spotify):
        """
        Call Spotify API to add songs to a playlist

        :param auth_code: (str) SpotifyAuth access_token for the given user
        :param playlist_id: (str) Spotify ID of the playlist to be created
        :param songs: (list) Collection of Spotify track URIs to add to playlist
        :param spotify: (spotify_client.SpotifyClient) Spotify Client instance
        """
        # Spotify has a limit of 100 songs per request to add songs to a playlist
        # Break up the total list of songs into batches of 100
        batched_songs = spotify.batch_tracks(songs)

        for batch in batched_songs:
            spotify.add_songs_to_playlist(auth_code, playlist_id, batch)

    @update_logging_data
    def upload_cover_image(self, auth_code, playlist_id, cover_image_filename, spotify, **kwargs):
        """
        Upload custom cover image for playlist. If any errors were encountered it will just fail
        silently.

        :param auth_code: (str) SpotifyAuth access_token for the given user
        :param playlist_id: (str) Spotify ID of the playlist to be created
        :param cover_image_filename: (str) Filename of cover image as a file on disk
        :param spotify: (spotify_client.SpotifyClient) Spotify Client instance
        """
        try:
            spotify.upload_image_to_playlist(auth_code, playlist_id, cover_image_filename)
        except (SpotifyException, ClientException):
            logger.warning(
                'Unable to upload cover image for playlist {}'.format(playlist_id),
                extra={
                    'fingerprint': auto_fingerprint('failed_upload_cover_image', **kwargs),
                    'trace_id': self.trace_id,
                },
                exc_info=True
            )

    @update_logging_data
    def run(self, auth_id, playlist_name, songs, cover_image_filename=None, *args, **kwargs):
        self.trace_id = kwargs.get('trace_id', '')
        auth = SpotifyAuth.get_and_refresh_spotify_auth_record(auth_id, trace_id=self.trace_id)

        # Check that user has granted proper scopes to export playlist to Spotify
        if not auth.has_scope(settings.SPOTIFY_PLAYLIST_MODIFY_SCOPE):
            logger.error(
                'User {} has not granted proper scopes to export playlist to Spotify'.format(auth.user.username),
                extra={
                    'fingerprint': auto_fingerprint('missing_scopes_for_playlist_export', **kwargs),
                    'auth_id': auth.pk,
                    'scopes': auth.scopes,
                    'trace_id': self.trace_id,
                }
            )

            raise InsufficientSpotifyScopesError('Insufficient Spotify scopes to export playlist')

        spotify = SpotifyClient(identifier='spotify.tasks.ExportSpotifyPlaylistFromSongsTask-{}'.format(self.trace_id))

        logger.info(
            'Exporting songs to playlist {} for user {} on Spotify'.format(playlist_name, auth.spotify_user_id),
            extra={
                'fingerprint': auto_fingerprint('start_export_playlist', **kwargs),
                'auth_id': auth.pk,
                'trace_id': self.trace_id,
            }
        )

        playlist_id = self.get_or_create_playlist(auth.access_token, auth.spotify_user_id, playlist_name, spotify)

        # Upload cover image for playlist if specified
        if auth.has_scope(settings.SPOTIFY_UPLOAD_PLAYLIST_IMAGE) and cover_image_filename:
            self.upload_cover_image(auth.access_token, playlist_id, cover_image_filename, spotify)

        self.delete_all_songs_from_playlist(auth.access_token, playlist_id, spotify)
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
                'auth_id': auth.pk,
                'trace_id': self.trace_id,
            }
        )


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
        trace_id = kwargs.get('trace_id', '')
        signature = 'spotify.tasks.FetchSongFromSpotifyTask-{}'.format(trace_id)

        # Early exit: if song already exists in our system don't do the work to fetch it
        if Song.objects.filter(code=spotify_code).exists():
            logger.info(
                'Song with code {} already exists in database'.format(spotify_code),
                extra={
                    'fingerprint': auto_fingerprint('song_already_exists', **kwargs),
                    'trace_id': trace_id,
                }
            )

            return

        client = SpotifyClient(identifier=signature)

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
                    'trace_id': trace_id,
                }
            )
        except ValidationError:
            logger.exception(
                'Failed to create song {}, already exists in database'.format(spotify_code),
                extra={
                    'fingerprint': auto_fingerprint('failed_to_create_song', **kwargs),
                    'trace_id': trace_id,
                }
            )

            raise
