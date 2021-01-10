from unittest import mock

from django.core.management import CommandError, call_command
from django.test import TestCase

from libs.tests.helpers import MoodyUtil
from spotify.models import SpotifyAuth


class TestCreateSpotifyAuthRecordsFromSpotifyUserAuthCommand(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()

        cls.test_spotify_user_id = 'test-spotify-user-id'
        cls.test_access_token = 'test-access-token'
        cls.test_refresh_token = 'test-access-token'

    @mock.patch('spotify.tasks.UpdateTopArtistsFromSpotifyTask.delay')
    @mock.patch('spotify.models.SpotifyAuth.refresh_access_token', mock.Mock())
    def test_happy_path(self, mock_update_top_artists_task):
        spotify_user_auth = MoodyUtil.create_spotify_user_auth(
            self.user,
            spotify_user_id=self.test_spotify_user_id,
            access_token=self.test_access_token,
            refresh_token=self.test_refresh_token
        )

        call_command('spotify_create_spotifyauth_records_from_spotifyuserauth_records')

        self.assertTrue(SpotifyAuth.objects.filter(user=self.user).exists())

        spotify_auth = SpotifyAuth.objects.get(user=self.user)
        mock_update_top_artists_task.assert_called_once_with(spotify_auth.pk)

        self.assertEqual(spotify_auth.user.pk, spotify_user_auth.user.pk)
        self.assertEqual(spotify_auth.spotify_user_id, spotify_user_auth.spotify_user_id)
        self.assertEqual(spotify_auth.access_token, spotify_user_auth.access_token)
        self.assertEqual(spotify_auth.refresh_token, spotify_user_auth.refresh_token)
        self.assertEqual(spotify_auth.scopes, spotify_user_auth.scopes)

    @mock.patch('spotify.models.SpotifyAuth.objects.create')
    def test_error_creating_spotify_auth_record_raises_command_error(self, mock_spotify_auth_create):
        MoodyUtil.create_spotify_user_auth(
            self.user,
            spotify_user_id=self.test_spotify_user_id,
            access_token=self.test_access_token,
            refresh_token=self.test_refresh_token
        )

        mock_spotify_auth_create.side_effect = Exception

        with self.assertRaises(CommandError):
            call_command('spotify_create_spotifyauth_records_from_spotifyuserauth_records')
