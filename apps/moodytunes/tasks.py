import logging

from django.core.exceptions import ValidationError

from accounts.models import SpotifyUserAuth
from base.tasks import MoodyBaseTask
from libs.moody_logging import auto_fingerprint, update_logging_data
from libs.spotify import SpotifyClient, SpotifyException
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

        client = SpotifyClient(identifier=signature)

        track_data = client.get_attributes_for_track(spotify_code)
        song_data = client.get_audio_features_for_tracks([track_data])[0]

        # Decode track data name/artist from unicode to string
        song_data['name'] = song_data['name'].decode('utf-8')
        song_data['artist'] = song_data['artist'].decode('utf-8')

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


class CreateSpotifyPlaylistFromSongsTask(MoodyBaseTask):
    default_retry_delay = 60 * 15
    autoretry_for = (SpotifyException,)

    @update_logging_data
    def get_or_create_playlist(self, auth_code, spotify_user_id, playlist_name, spotify, **kwargs):
        """
        Get the Spotify playlist by name for the user, creating it if it does not exist

        :param auth_code: (str) SpotifyUserAuth access_token for the given user
        :param spotify_user_id: (str) Spotify username for the given user
        :param playlist_name: (str) Name of the playlist to be created
        :param spotify: (libs.spotify.SpotifyClient) Spotify Client instance

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
            logger.warning('Error getting playlists for user {}'.format(spotify_user_id), extra={
                'fingerprint': auto_fingerprint('failed_getting_user_playlists', **kwargs),
                'spotify_user_id': spotify_user_id,
                'playlist_name': playlist_name,
            })

        if playlist_id is None:
            playlist_id = spotify.create_playlist(auth_code, spotify_user_id, playlist_name)
            logger.info(
                'Created playlist for user {} with name {} successfully'.format(spotify_user_id, playlist_name),
                extra={'fingerprint': auto_fingerprint('created_spotify_playlist', **kwargs)}
            )

        return playlist_id

    @update_logging_data
    def add_songs_to_playlist(self, auth_code, playlist_id, songs, spotify, **kwargs):
        """
        Call Spotify API to add songs to a playlist

        :param auth_code: (str) SpotifyUserAuth access_token for the given user
        :param playlist_id: (str) Spotify ID of the playlist to be created
        :param songs: (list) Collection of Spotify track URIs to add to playlist
        :param spotify: (libs.spotify.SpotifyClient) Spotify Client instance

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
    def run(self, auth_id, playlist_name, songs, *args, **kwargs):
        auth = SpotifyUserAuth.get_and_refresh_spotify_user_auth_record(auth_id)

        spotify = SpotifyClient(identifier='create_spotify_playlist_from_songs_{}'.format(auth.spotify_user_id))

        logger.info(
            'Exporting songs to playlist {} for user {} on Spotify'.format(playlist_name, auth.user.username),
            extra={
                'fingerprint': auto_fingerprint('start_export_playlist', **kwargs),
                'songs': songs,
                'auth_id': auth.pk
            }
        )

        playlist_id = self.get_or_create_playlist(auth.access_token, auth.spotify_user_id, playlist_name, spotify)
        self.add_songs_to_playlist(auth.access_token, playlist_id, songs, spotify)

        logger.info(
            'Exported songs to playlist {} successfully'.format(playlist_name),
            extra={
                'fingerprint': auto_fingerprint('success_export_playlist', **kwargs),
                'songs': songs,
                'auth_id': auth.pk
            }
        )
