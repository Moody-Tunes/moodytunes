from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase
from spotify_client.exceptions import ClientException, SpotifyException

from accounts.exceptions import InsufficientSpotifyScopesError
from accounts.models import SpotifyUserAuth
from libs.tests.helpers import MoodyUtil, generate_random_unicode_string
from moodytunes.tasks import ExportSpotifyPlaylistFromSongsTask, FetchSongFromSpotifyTask
from tunes.models import Song


class TestFetchSongFromSpotify(TestCase):
    @mock.patch('spotify_client.SpotifyClient.get_audio_features_for_tracks')
    @mock.patch('spotify_client.SpotifyClient.get_attributes_for_track')
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
    @mock.patch('spotify_client.SpotifyClient.get_attributes_for_track')
    def test_task_is_retried_on_spotify_error(self, mock_get_attributes, mock_retry):
        mock_get_attributes.side_effect = SpotifyException
        song_code = 'spotify:track:1234567'

        FetchSongFromSpotifyTask().run(song_code)

        mock_retry.assert_called_once()

    @mock.patch('spotify_client.SpotifyClient.get_audio_features_for_tracks')
    @mock.patch('spotify_client.SpotifyClient.get_attributes_for_track')
    def test_task_does_not_call_spotify_if_song_already_exists(self, mock_get_attributes, mock_get_features):
        song = MoodyUtil.create_song()

        FetchSongFromSpotifyTask().run(song.code)

        mock_get_attributes.assert_not_called()
        mock_get_features.assert_not_called()

    @mock.patch('tunes.models.Song.objects.create')
    @mock.patch('spotify_client.SpotifyClient.get_audio_features_for_tracks')
    @mock.patch('spotify_client.SpotifyClient.get_attributes_for_track')
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

    @mock.patch('spotify_client.SpotifyClient.get_audio_features_for_tracks')
    @mock.patch('spotify_client.SpotifyClient.get_attributes_for_track')
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


class TestExportSpotifyPlaylistFromSongs(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.auth = MoodyUtil.create_spotify_user_auth(cls.user)

        cls.playlist_name = 'new_playlist'
        cls.playlist_id = 'spotify:playlist:id'

        cls.songs = []

        for i in range(30):
            cls.songs.append(MoodyUtil.create_song().code)

    @mock.patch('spotify_client.SpotifyClient.delete_songs_from_playlist', mock.Mock())
    @mock.patch('spotify_client.SpotifyClient.get_all_songs_from_user_playlist', mock.Mock(return_value=[]))
    @mock.patch('spotify_client.SpotifyClient.add_songs_to_playlist')
    @mock.patch('spotify_client.SpotifyClient.create_playlist')
    @mock.patch('spotify_client.SpotifyClient.get_user_playlists')
    def test_happy_path(
            self,
            mock_get_user_playlists,
            mock_create_playlist,
            mock_add_songs_to_playlist,
    ):
        mock_get_user_playlists.return_value = {'items': []}
        mock_create_playlist.return_value = self.playlist_id

        ExportSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs)

        mock_create_playlist.assert_called_once_with(
            self.auth.access_token,
            self.auth.spotify_user_id,
            self.playlist_name
        )
        mock_add_songs_to_playlist.assert_called_once_with(self.auth.access_token, self.playlist_id, self.songs)

    @mock.patch('spotify_client.SpotifyClient.add_songs_to_playlist', mock.Mock())
    @mock.patch('spotify_client.SpotifyClient.create_playlist', mock.Mock())
    @mock.patch('spotify_client.SpotifyClient.delete_songs_from_playlist')
    @mock.patch('spotify_client.SpotifyClient.get_all_songs_from_user_playlist')
    @mock.patch('spotify_client.SpotifyClient.get_user_playlists')
    def test_task_deletes_all_songs_from_playlist_if_songs_found(
            self,
            mock_get_user_playlists,
            mock_get_songs_from_playlist,
            mock_delete_songs_from_playlist,
    ):
        playlist_id = 'spotify:playlist:id'
        mock_get_user_playlists.return_value = {'items': [{'name': self.playlist_name, 'id': playlist_id}]}

        mock_get_songs_from_playlist.return_value = self.songs

        ExportSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs)

        mock_get_songs_from_playlist.assert_called_once_with(self.auth.access_token, playlist_id)
        mock_delete_songs_from_playlist.assert_called_once_with(self.auth.access_token, playlist_id, self.songs)

    @mock.patch('spotify_client.SpotifyClient.add_songs_to_playlist', mock.Mock())
    @mock.patch('spotify_client.SpotifyClient.create_playlist', mock.Mock())
    @mock.patch('spotify_client.SpotifyClient.delete_songs_from_playlist')
    @mock.patch('spotify_client.SpotifyClient.get_all_songs_from_user_playlist')
    @mock.patch('spotify_client.SpotifyClient.get_user_playlists')
    def test_task_does_not_delete_songs_from_playlist_if_playlist_is_empty(
            self,
            mock_get_user_playlists,
            mock_get_songs_from_playlist,
            mock_delete_songs_from_playlist,
    ):
        mock_get_user_playlists.return_value = {'items': [{'name': self.playlist_name, 'id': self.playlist_id}]}

        mock_get_songs_from_playlist.return_value = []

        ExportSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs)

        mock_get_songs_from_playlist.assert_called_once_with(self.auth.access_token, self.playlist_id)
        mock_delete_songs_from_playlist.assert_not_called()

    @mock.patch('moodytunes.tasks.ExportSpotifyPlaylistFromSongsTask.retry')
    @mock.patch('spotify_client.SpotifyClient.create_playlist')
    @mock.patch('spotify_client.SpotifyClient.get_user_playlists')
    def test_error_creating_playlist_retries(
            self,
            mock_get_user_playlists,
            mock_create_playlist,
            mock_retry
    ):
        mock_get_user_playlists.return_value = {'items': []}

        mock_create_playlist.side_effect = SpotifyException

        ExportSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs)

        mock_retry.assert_called_once()

    @mock.patch('spotify_client.SpotifyClient.get_all_songs_from_user_playlist', mock.Mock(return_value=[]))
    @mock.patch('spotify_client.SpotifyClient.delete_songs_from_playlist', mock.Mock())
    @mock.patch('moodytunes.tasks.ExportSpotifyPlaylistFromSongsTask.retry')
    @mock.patch('spotify_client.SpotifyClient.add_songs_to_playlist')
    @mock.patch('spotify_client.SpotifyClient.create_playlist')
    @mock.patch('spotify_client.SpotifyClient.get_user_playlists')
    def test_error_adding_songs_to_playlist_retries(
            self,
            mock_get_user_playlists,
            mock_create_playlist,
            mock_add_songs_to_playlist,
            mock_retry
    ):
        mock_get_user_playlists.return_value = {'items': []}
        mock_create_playlist.return_value = self.playlist_id

        mock_add_songs_to_playlist.side_effect = SpotifyException

        ExportSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs)

        mock_retry.assert_called_once()

    @mock.patch('spotify_client.SpotifyClient.get_all_songs_from_user_playlist', mock.Mock(return_value=[]))
    @mock.patch('spotify_client.SpotifyClient.delete_songs_from_playlist', mock.Mock())
    @mock.patch('spotify_client.SpotifyClient.add_songs_to_playlist')
    @mock.patch('spotify_client.SpotifyClient.create_playlist')
    @mock.patch('spotify_client.SpotifyClient.get_user_playlists')
    def test_found_playlist_does_not_create_new_playlist(
            self,
            mock_get_user_playlists,
            mock_create_playlist,
            mock_add_songs_to_playlist,
    ):
        mock_get_user_playlists.return_value = {'items': [{'name': self.playlist_name, 'id': self.playlist_id}]}

        ExportSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs)

        mock_get_user_playlists.assert_called_once_with(self.auth.access_token, self.auth.spotify_user_id)
        mock_create_playlist.assert_not_called()
        mock_add_songs_to_playlist.assert_called_once_with(self.auth.access_token, self.playlist_id, self.songs)

    @mock.patch('spotify_client.SpotifyClient.get_all_songs_from_user_playlist', mock.Mock(return_value=[]))
    @mock.patch('spotify_client.SpotifyClient.delete_songs_from_playlist', mock.Mock())
    @mock.patch('spotify_client.SpotifyClient.add_songs_to_playlist')
    @mock.patch('spotify_client.SpotifyClient.create_playlist')
    @mock.patch('spotify_client.SpotifyClient.get_user_playlists')
    def test_playlist_not_found_creates_new_playlist(
            self,
            mock_get_user_playlists,
            mock_create_playlist,
            mock_add_songs_to_playlist,
    ):
        mock_get_user_playlists.return_value = {'items': [{'name': 'some_other_playlist', 'id': '12345'}]}
        mock_create_playlist.return_value = self.playlist_id

        ExportSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs)

        mock_get_user_playlists.assert_called_once_with(self.auth.access_token, self.auth.spotify_user_id)
        mock_create_playlist.assert_called_once_with(
            self.auth.access_token,
            self.auth.spotify_user_id,
            self.playlist_name
        )
        mock_add_songs_to_playlist.assert_called_once_with(self.auth.access_token, self.playlist_id, self.songs)

    @mock.patch('spotify_client.SpotifyClient.get_all_songs_from_user_playlist', mock.Mock(return_value=[]))
    @mock.patch('spotify_client.SpotifyClient.delete_songs_from_playlist', mock.Mock())
    @mock.patch('spotify_client.SpotifyClient.add_songs_to_playlist')
    @mock.patch('spotify_client.SpotifyClient.create_playlist')
    @mock.patch('spotify_client.SpotifyClient.get_user_playlists')
    def test_error_finding_playlist_creates_new_playlist(
            self,
            mock_get_user_playlists,
            mock_create_playlist,
            mock_add_songs_to_playlist,
    ):
        mock_get_user_playlists.side_effect = SpotifyException
        mock_create_playlist.return_value = self.playlist_id

        ExportSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs)

        mock_create_playlist.assert_called_once_with(
            self.auth.access_token,
            self.auth.spotify_user_id,
            self.playlist_name
        )
        mock_add_songs_to_playlist.assert_called_once_with(self.auth.access_token, self.playlist_id, self.songs)

    @mock.patch('spotify_client.SpotifyClient.get_all_songs_from_user_playlist', mock.Mock(return_value=[]))
    @mock.patch('spotify_client.SpotifyClient.delete_songs_from_playlist', mock.Mock())
    @mock.patch('spotify_client.SpotifyClient.add_songs_to_playlist', mock.Mock())
    @mock.patch('spotify_client.SpotifyClient.upload_image_to_playlist')
    @mock.patch('spotify_client.SpotifyClient.create_playlist')
    @mock.patch('spotify_client.SpotifyClient.get_user_playlists')
    def test_upload_image_for_playlist_called_if_image_provided(
            self,
            mock_get_user_playlists,
            mock_create_playlist,
            mock_upload_cover_image
    ):
        cover_image_filename = 'cover_image.jpg'
        mock_get_user_playlists.return_value = {'items': []}
        mock_create_playlist.return_value = self.playlist_id

        ExportSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs, cover_image_filename)

        mock_upload_cover_image.assert_called_once_with(self.auth.access_token, self.playlist_id, cover_image_filename)

    @mock.patch('spotify_client.SpotifyClient.get_all_songs_from_user_playlist', mock.Mock(return_value=[]))
    @mock.patch('spotify_client.SpotifyClient.delete_songs_from_playlist', mock.Mock())
    @mock.patch('spotify_client.SpotifyClient.upload_image_to_playlist')
    @mock.patch('spotify_client.SpotifyClient.add_songs_to_playlist')
    @mock.patch('spotify_client.SpotifyClient.create_playlist')
    @mock.patch('spotify_client.SpotifyClient.get_user_playlists')
    def test_playlist_is_exported_if_upload_image_raises_spotify_exception(
            self,
            mock_get_user_playlists,
            mock_create_playlist,
            mock_add_songs_to_playlist,
            mock_upload_cover_image
    ):
        cover_image_filename = 'cover_image.jpg'
        mock_upload_cover_image.side_effect = SpotifyException

        mock_get_user_playlists.return_value = {'items': []}
        mock_create_playlist.return_value = self.playlist_id

        ExportSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs, cover_image_filename)

        mock_add_songs_to_playlist.assert_called_once_with(self.auth.access_token, self.playlist_id, self.songs)

    @mock.patch('spotify_client.SpotifyClient.get_all_songs_from_user_playlist', mock.Mock(return_value=[]))
    @mock.patch('spotify_client.SpotifyClient.delete_songs_from_playlist', mock.Mock())
    @mock.patch('spotify_client.SpotifyClient.upload_image_to_playlist')
    @mock.patch('spotify_client.SpotifyClient.add_songs_to_playlist')
    @mock.patch('spotify_client.SpotifyClient.create_playlist')
    @mock.patch('spotify_client.SpotifyClient.get_user_playlists')
    def test_playlist_is_exported_if_upload_image_raises_client_exception(
            self,
            mock_get_user_playlists,
            mock_create_playlist,
            mock_add_songs_to_playlist,
            mock_upload_cover_image
    ):
        cover_image_filename = 'cover_image.jpg'
        mock_upload_cover_image.side_effect = ClientException

        mock_get_user_playlists.return_value = {'items': []}
        mock_create_playlist.return_value = self.playlist_id

        ExportSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs, cover_image_filename)

        mock_add_songs_to_playlist.assert_called_once_with(self.auth.access_token, self.playlist_id, self.songs)

    @mock.patch('spotify_client.SpotifyClient.get_all_songs_from_user_playlist', mock.Mock(return_value=[]))
    @mock.patch('spotify_client.SpotifyClient.delete_songs_from_playlist', mock.Mock())
    @mock.patch('spotify_client.SpotifyClient.add_songs_to_playlist', mock.Mock())
    @mock.patch('spotify_client.SpotifyClient.upload_image_to_playlist')
    @mock.patch('spotify_client.SpotifyClient.create_playlist')
    @mock.patch('spotify_client.SpotifyClient.get_user_playlists')
    def test_upload_image_for_playlist_not_called_if_user_does_not_have_proper_scope(
            self,
            mock_get_user_playlists,
            mock_create_playlist,
            mock_upload_cover_image
    ):
        cover_image_filename = 'cover_image.jpg'
        mock_get_user_playlists.return_value = {'items': []}

        self.auth.scopes = ["playlist-modify-public", "user-top-read"]
        self.auth.save()

        mock_create_playlist.return_value = self.playlist_id

        ExportSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs, cover_image_filename)

        mock_upload_cover_image.assert_not_called()

    def test_get_auth_record_does_not_exists_raises_error(self):
        invalid_auth_id = 99999

        with self.assertRaises(SpotifyUserAuth.DoesNotExist):
            ExportSpotifyPlaylistFromSongsTask().run(invalid_auth_id, self.playlist_name, self.songs)

    @mock.patch('moodytunes.tasks.ExportSpotifyPlaylistFromSongsTask.retry')
    @mock.patch('accounts.models.SpotifyUserAuth.refresh_access_token')
    @mock.patch('accounts.models.SpotifyUserAuth.should_refresh_access_token')
    def test_get_auth_record_error_on_refresh_access_token_retries(
            self,
            mock_should_refresh_access_token,
            mock_refresh_access_token,
            mock_retry
    ):
        mock_should_refresh_access_token.return_value = True
        mock_refresh_access_token.side_effect = SpotifyException

        ExportSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs)

        mock_retry.assert_called_once()

    def test_missing_required_scopes_raises_error(self):
        self.auth.scopes = []
        self.auth.save()

        with self.assertRaises(InsufficientSpotifyScopesError):
            ExportSpotifyPlaylistFromSongsTask().run(self.auth.id, self.playlist_name, self.songs)
