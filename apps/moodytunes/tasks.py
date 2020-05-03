import logging

from accounts.models import SpotifyUserAuth
from base.tasks import MoodyBaseTask
from tunes.models import Song
from libs.spotify import SpotifyClient, SpotifyException


logger = logging.getLogger(__name__)


class FetchSongFromSpotifyTask(MoodyBaseTask):
    max_retries = 3
    default_retry_delay = 60 * 15

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
                extra={'fingerprint': signature}
            )
            return

        client = SpotifyClient(identifier=signature)
        song_data = None

        try:
            logger.info(
                'Making request to Spotify for song data for {}'.format(spotify_code),
                extra={'fingerprint': signature}
            )
            track_data = client.get_attributes_for_track(spotify_code)
            song_data = client.get_audio_features_for_tracks([track_data])[0]
        except SpotifyException:
            logger.warning(
                'Failed to fetch song data from Spotify. Retrying',
                extra={'fingerprint': signature},
                exc_info=True
            )
            self.retry()

        if song_data:
            # Decode track data name/artist from unicode to string
            song_data['name'] = song_data['name'].decode('utf-8')
            song_data['artist'] = song_data['artist'].decode('utf-8')
            _, created = Song.objects.get_or_create(code=song_data['code'], defaults=song_data)

            if created:
                logger.info(
                    'Created song {} in database'.format(spotify_code),
                    extra={'fingerprint': signature}
                )
            else:
                logger.info(
                    'Did not create song {} in database, song already exists'.format(spotify_code),
                    extra={'fingerprint': signature}
                )


class CreateSpotifyPlaylistFromSongsTask(MoodyBaseTask):
    max_retries = 3
    default_retry_delay = 60 * 15

    fingerprint_base = 'tunes.tasks.CreateSpotifyPlaylistFromSongsTask.{msg}'

    def get_or_create_playlist(self, auth_code, spotify_user_id, playlist_name, spotify):
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
            logger.info('Checking if user {} has playlist with name {}'.format(spotify_user_id, playlist_name))
            resp = spotify.get_user_playlists(auth_code, spotify_user_id)
            playlists = resp['items']

            for playlist in playlists:
                if playlist['name'] == playlist_name:
                    playlist_id = playlist['id']
                    break

        except SpotifyException:
            logger.warning('Error getting playlists for user {}'.format(spotify_user_id), extra={
                'fingerprint': self.fingerprint_base.format(msg='failed_getting_user_playlists'),
                'spotify_user_id': spotify_user_id,
                'playlist_name': playlist_name,
            })

        if playlist_id is None:
            try:
                logger.info('Creating playlist for user {} with name {}'.format(spotify_user_id, playlist_name))
                playlist_id = spotify.create_playlist(auth_code, spotify_user_id, playlist_name)
                logger.info(
                    'Created playlist for user {} with name {} successfully'.format(spotify_user_id, playlist_name),
                    extra={'fingerprint': self.fingerprint_base.format(msg='created_spotify_playlist')}
                )

            except SpotifyException:
                logger.exception('Error creating playlist for user {}'.format(spotify_user_id), extra={
                    'fingerprint': self.fingerprint_base.format(msg='failed_creating_playlist'),
                    'spotify_user_id': spotify_user_id,
                    'playlist_name': playlist_name,
                })
                self.retry()

        return playlist_id

    def add_songs_to_playlist(self, auth_code, playlist_id, songs, spotify):
        """
        Call Spotify API to add songs to a playlist

        :param auth_code: (str) SpotifyUserAuth access_token for the given user
        :param playlist_id: (str) Spotify ID of the playlist to be created
        :param songs: (list) Collection of Spotify track URIs to add to playlist
        :param spotify: (libs.spotify.SpotifyClient) Spotify Client instance

        """
        try:
            logger.info('Adding songs to playlist {}'.format(playlist_id))

            # Spotify has a limit of 100 songs per request to add songs to a playlist
            # Break up the total list of songs into batches of 100
            batched_songs = spotify.batch_tracks(songs)

            # First, remove songs from playlist to clear out already existing songs
            for batch in batched_songs:
                spotify.delete_songs_from_playlist(auth_code, playlist_id, batch)

            for batch in batched_songs:
                spotify.add_songs_to_playlist(auth_code, playlist_id, batch)

            logger.info(
                'Added songs to playlist {} successfully'.format(playlist_id),
                extra={'fingerprint': self.fingerprint_base.format(msg='success_adding_songs_to_spotify_playlist')}
            )
        except SpotifyException:
            logger.exception(
                'Error adding songs to playlist {}'.format(playlist_id), extra={
                    'fingerprint': self.fingerprint_base.format(msg='failed_adding_songs_to_playlist'),
                    'songs': songs
                }
            )
            self.retry()

    def get_and_refresh_spotify_user_auth_record(self, auth_id):
        """
        Fetch the SpotifyUserAuth record for the given primary key, and refresh if
        the access token is expired

        :param auth_id: (int) Primary key for SpotifyUserAuth record

        :return: (SpotifyUserAuth)
        """
        try:
            auth = SpotifyUserAuth.objects.get(pk=auth_id)
        except (SpotifyUserAuth.MultipleObjectsReturned, SpotifyUserAuth.DoesNotExist):
            logger.error(
                'Failed to fetch SpotifyUserAuth with pk={}'.format(auth_id),
                extra={'fingerprint': self.fingerprint_base.format(msg='fail_fetch_spotify_auth_user')}
            )

            raise

        if auth.should_update_access_token:
            try:
                auth.refresh_access_token()
            except SpotifyException:
                logger.warning(
                    'Failed to update access token for SpotifyUserAuth with pk={}'.format(auth_id),
                    extra={'fingerprint': self.fingerprint_base.format(msg='failed_update_access_token')}
                )

                self.retry()

        return auth

    def run(self, auth_id, playlist_name, songs, *args, **kwargs):
        auth = self.get_and_refresh_spotify_user_auth_record(auth_id)
        spotify = SpotifyClient(identifier='create_spotify_playlist_from_songs_{}'.format(auth.spotify_user_id))

        playlist_id = self.get_or_create_playlist(auth.access_token, auth.spotify_user_id, playlist_name, spotify)
        self.add_songs_to_playlist(auth.access_token, playlist_id, songs, spotify)
