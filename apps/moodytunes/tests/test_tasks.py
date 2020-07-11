from datetime import timedelta
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import SpotifyUserAuth
from libs.spotify import SpotifyException
from libs.tests.helpers import MoodyUtil, generate_random_unicode_string
from moodytunes.tasks import CreateSpotifyPlaylistFromSongsTask, FetchSongFromSpotifyTask
from tunes.models import Song


class TestFetchSongFromSpotify(TestCase):
    @mock.patch('libs.spotify.SpotifyClient.get_audio_features_for_tracks')
    @mock.patch('libs.spotify.SpotifyClient.get_attributes_for_track')
    def test_happy_path(self, mock_get_attributes, mock_get_features):
        song_code = 'spotify:track:1234567'

        mock_get_attributes.return_value = {
            'code': song_code,
            'name': 'Sickfit',
            'artist': 'Madlib'
        }

        mock_get_features.return_value = [{
            'code': song_code,
            'name': 'Sickfit',
            'artist': 'Madlib',
            'valence': .5,
            'energy': .5
        }]

        FetchSongFromSpotifyTask().run(song_code)

        self.assertTrue(Song.objects.filter(code=song_code).exists())

    @mock.patch('moodytunes.tasks.FetchSongFromSpotifyTask.retry')
    @mock.patch('libs.spotify.SpotifyClient.get_attributes_for_track')
    def test_task_is_retried_on_spotify_error(self, mock_get_attributes, mock_retry):
        mock_get_attributes.side_effect = SpotifyException
        song_code = 'spotify:track:1234567'

        FetchSongFromSpotifyTask().run(song_code)

        mock_retry.assert_called_once()

    @mock.patch('libs.spotify.SpotifyClient.get_audio_features_for_tracks')
    @mock.patch('libs.spotify.SpotifyClient.get_attributes_for_track')
    def test_task_does_not_call_spotify_if_song_already_exists(self, mock_get_attributes, mock_get_features):
        song = MoodyUtil.create_song()

        FetchSongFromSpotifyTask().run(song.code)

        mock_get_attributes.assert_not_called()
        mock_get_features.assert_not_called()

    @mock.patch('tunes.models.Song.objects.create')
    @mock.patch('libs.spotify.SpotifyClient.get_audio_features_for_tracks')
    @mock.patch('libs.spotify.SpotifyClient.get_attributes_for_track')
    def test_validation_error_on_song_create_raises_exception(
            self,
            mock_get_attributes,
            mock_get_features,
            mock_song_create
    ):
        song_code = 'spotify:track:1234567'

        mock_get_attributes.return_value = {
            'code': song_code,
            'name': 'Sickfit',
            'artist': 'Madlib'
        }

        mock_get_features.return_value = [{
            'code': song_code,
            'name': 'Sickfit',
            'artist': 'Madlib',
            'valence': .5,
            'energy': .5
        }]

        mock_song_create.side_effect = ValidationError('Oops!')

        with self.assertRaises(ValidationError):
            FetchSongFromSpotifyTask().run(song_code)

    @mock.patch('libs.spotify.SpotifyClient.get_audio_features_for_tracks')
    @mock.patch('libs.spotify.SpotifyClient.get_attributes_for_track')
    def test_task_handles_song_with_unicode_data(self, mock_get_attributes, mock_get_features):
        song_code = 'spotify:track:1234567'
        song_name = generate_random_unicode_string(10)
        song_artist = generate_random_unicode_string(10)

        mock_get_attributes.return_value = {
            'code': song_code,
            'name': song_name,
            'artist': song_artist
        }

        mock_get_features.return_value = [{
            'code': song_code,
            'name': song_name,
            'artist': song_artist,
            'valence': .5,
            'energy': .5
        }]

        FetchSongFromSpotifyTask().run(song_code)

        self.assertTrue(Song.objects.filter(code=song_code).exists())


class TestCreateSpotifyPlaylistFromSongs(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.auth = MoodyUtil.create_spotify_user_auth(cls.user)
        cls.playlist_name = 'new_playlist'
        cls.songs = ['spotify:track:1']

    @mock.patch('libs.spotify.SpotifyClient.delete_songs_from_playlist')
    @mock.patch('libs.spotify.SpotifyClient.add_songs_to_playlist')
    @mock.patch('libs.spotify.SpotifyClient.create_playlist')
    @mock.patch('libs.spotify.SpotifyClient.get_user_playlists')
    def test_happy_path(
            self,
            mock_get_user_playlists,
            mock_create_playlist,
            mock_add_songs_to_playlist,
            mock_delete_songs_from_playlist,
    ):
        mock_get_user_playlists.return_value = {'items': []}

        playlist_id = 'spotify:playlist:id'
        mock_create_playlist.return_value = playlist_id

        CreateSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs)

        mock_create_playlist.assert_called_once_with(
            self.auth.access_token,
            self.auth.spotify_user_id,
            self.playlist_name
        )
        mock_add_songs_to_playlist.assert_called_once_with(self.auth.access_token, playlist_id, self.songs)

    @mock.patch('moodytunes.tasks.CreateSpotifyPlaylistFromSongsTask.retry')
    @mock.patch('libs.spotify.SpotifyClient.delete_songs_from_playlist')
    @mock.patch('libs.spotify.SpotifyClient.add_songs_to_playlist')
    @mock.patch('libs.spotify.SpotifyClient.create_playlist')
    @mock.patch('libs.spotify.SpotifyClient.get_user_playlists')
    def test_error_creating_playlist_retries(
            self,
            mock_get_user_playlists,
            mock_create_playlist,
            mock_add_songs_to_playlist,
            mock_delete_songs_from_playlist,
            mock_retry
    ):
        mock_get_user_playlists.return_value = {'items': []}

        mock_create_playlist.side_effect = SpotifyException

        CreateSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs)

        mock_retry.assert_called_once()

    @mock.patch('moodytunes.tasks.CreateSpotifyPlaylistFromSongsTask.retry')
    @mock.patch('libs.spotify.SpotifyClient.delete_songs_from_playlist')
    @mock.patch('libs.spotify.SpotifyClient.add_songs_to_playlist')
    @mock.patch('libs.spotify.SpotifyClient.create_playlist')
    @mock.patch('libs.spotify.SpotifyClient.get_user_playlists')
    def test_error_adding_songs_to_playlist_retries(
            self,
            mock_get_user_playlists,
            mock_create_playlist,
            mock_add_songs_to_playlist,
            mock_delete_songs_from_playlist,
            mock_retry
    ):
        mock_get_user_playlists.return_value = {'items': []}

        playlist_id = 'spotify:playlist:id'
        mock_create_playlist.return_value = playlist_id

        mock_add_songs_to_playlist.side_effect = SpotifyException

        CreateSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs)

        mock_retry.assert_called_once()

    @mock.patch('libs.spotify.SpotifyClient.delete_songs_from_playlist')
    @mock.patch('libs.spotify.SpotifyClient.add_songs_to_playlist')
    @mock.patch('libs.spotify.SpotifyClient.create_playlist')
    @mock.patch('libs.spotify.SpotifyClient.get_user_playlists')
    def test_found_playlist_does_not_create_new_playlist(
            self,
            mock_get_user_playlists,
            mock_create_playlist,
            mock_add_songs_to_playlist,
            mock_delete_songs_from_playlist,
    ):
        playlist_id = 'spotify:playlist:id'
        mock_get_user_playlists.return_value = {'items': [{'name': self.playlist_name, 'id': playlist_id}]}

        CreateSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs)

        mock_get_user_playlists.assert_called_once_with(self.auth.access_token, self.auth.spotify_user_id)
        mock_create_playlist.assert_not_called()
        mock_add_songs_to_playlist.assert_called_once_with(self.auth.access_token, playlist_id, self.songs)

    @mock.patch('libs.spotify.SpotifyClient.delete_songs_from_playlist')
    @mock.patch('libs.spotify.SpotifyClient.add_songs_to_playlist')
    @mock.patch('libs.spotify.SpotifyClient.create_playlist')
    @mock.patch('libs.spotify.SpotifyClient.get_user_playlists')
    def test_playlist_not_found_creates_new_playlist(
            self,
            mock_get_user_playlists,
            mock_create_playlist,
            mock_add_songs_to_playlist,
            mock_delete_songs_from_playlist,
    ):
        playlist_id = 'spotify:playlist:id'
        mock_get_user_playlists.return_value = {'items': [{'name': 'some_other_playlist', 'id': '12345'}]}

        mock_create_playlist.return_value = playlist_id

        CreateSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs)

        mock_get_user_playlists.assert_called_once_with(self.auth.access_token, self.auth.spotify_user_id)
        mock_create_playlist.assert_called_once_with(
            self.auth.access_token,
            self.auth.spotify_user_id,
            self.playlist_name
        )
        mock_add_songs_to_playlist.assert_called_once_with(self.auth.access_token, playlist_id, self.songs)

    @mock.patch('libs.spotify.SpotifyClient.delete_songs_from_playlist')
    @mock.patch('libs.spotify.SpotifyClient.add_songs_to_playlist')
    @mock.patch('libs.spotify.SpotifyClient.create_playlist')
    @mock.patch('libs.spotify.SpotifyClient.get_user_playlists')
    def test_error_finding_playlist_creates_new_playlist(
            self,
            mock_get_user_playlists,
            mock_create_playlist,
            mock_add_songs_to_playlist,
            mock_delete_songs_from_playlist,
    ):
        mock_get_user_playlists.side_effect = SpotifyException

        playlist_id = 'spotify:playlist:id'
        mock_create_playlist.return_value = playlist_id

        CreateSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs)

        mock_create_playlist.assert_called_once_with(
            self.auth.access_token,
            self.auth.spotify_user_id,
            self.playlist_name
        )
        mock_add_songs_to_playlist.assert_called_once_with(self.auth.access_token, playlist_id, self.songs)

    def test_get_auth_record_does_not_exists_raises_error(self):
        invalid_auth_id = 99999

        with self.assertRaises(SpotifyUserAuth.DoesNotExist):
            CreateSpotifyPlaylistFromSongsTask().run(invalid_auth_id, self.playlist_name, self.songs)

    @mock.patch('moodytunes.tasks.CreateSpotifyPlaylistFromSongsTask.retry')
    @mock.patch('libs.spotify.SpotifyClient.refresh_access_token')
    def test_get_auth_record_error_on_refresh_access_tokens_retries(self, mock_refresh_access_token, mock_retry):
        self.auth.last_refreshed = timezone.now() - timedelta(days=1)
        self.auth.save()

        mock_refresh_access_token.side_effect = SpotifyException

        CreateSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs)

        mock_retry.assert_called_once()
