from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from spotify.models import SpotifyAuth
from spotify_client.exceptions import SpotifyException

from libs.tests.helpers import MoodyUtil


class TestSpotifyAuth(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()

    def test_should_refresh_access_token_returns_false_for_recently_created_records(self):
        user_auth = MoodyUtil.create_spotify_auth(self.user)
        self.assertFalse(user_auth.should_refresh_access_token)

    def test_should_refresh_access_token_returns_false_for_tokens_refreshed_in_boundary(self):
        user_auth = MoodyUtil.create_spotify_auth(self.user)
        user_auth.last_refreshed = timezone.now() - timedelta(minutes=30)

        self.assertFalse(user_auth.should_refresh_access_token)

    def test_should_refreshed_access_token_returns_true_for_tokens_refreshed_passed_boundary(self):
        user_auth = MoodyUtil.create_spotify_auth(self.user)
        user_auth.last_refreshed = timezone.now() - timedelta(days=7)

        self.assertTrue(user_auth.should_refresh_access_token)

    def test_encrypted_fields_return_values_on_access(self):
        access_token = 'access:token'
        refresh_token = 'refresh_token'
        user_auth = MoodyUtil.create_spotify_auth(
            self.user,
            access_token=access_token,
            refresh_token=refresh_token
        )

        self.assertEqual(user_auth.access_token, access_token)
        self.assertEqual(user_auth.refresh_token, refresh_token)

    @mock.patch('spotify_client.SpotifyClient.refresh_access_token')
    def test_refresh_access_token_happy_path(self, mock_refresh_access_token):
        refresh_access_token = 'mock:spotify:access:token'
        mock_refresh_access_token.return_value = refresh_access_token

        access_token = 'access:token'
        refresh_token = 'refresh_token'
        user_auth = MoodyUtil.create_spotify_auth(
            self.user,
            access_token=access_token,
            refresh_token=refresh_token
        )

        old_last_refreshed = user_auth.last_refreshed

        user_auth.refresh_access_token()
        user_auth.refresh_from_db()

        self.assertEqual(user_auth.access_token, refresh_access_token)
        self.assertGreater(user_auth.last_refreshed, old_last_refreshed)

    @mock.patch('spotify_client.SpotifyClient.refresh_access_token')
    def test_refresh_access_token_raises_exception(self, mock_refresh_access_token):
        mock_refresh_access_token.side_effect = SpotifyException

        access_token = 'access:token'
        refresh_token = 'refresh_token'
        user_auth = MoodyUtil.create_spotify_auth(
            self.user,
            access_token=access_token,
            refresh_token=refresh_token
        )

        with self.assertRaises(SpotifyException):
            user_auth.refresh_access_token()

    def test_get_and_refresh_spotify_user_auth_record_happy_path(self):
        user_auth = MoodyUtil.create_spotify_auth(self.user)
        retrieved_user_auth = SpotifyAuth.get_and_refresh_spotify_auth_record(user_auth.id)

        self.assertEqual(user_auth.pk, retrieved_user_auth.pk)

    @mock.patch('spotify_client.SpotifyClient.refresh_access_token')
    def test_get_and_refresh_spotify_user_auth_record_refreshes_access_token_if_needed(self, mock_refresh_access_token):
        refresh_access_token = 'mock:spotify:access:token'
        mock_refresh_access_token.return_value = refresh_access_token

        user_auth = MoodyUtil.create_spotify_auth(self.user)
        user_auth.last_refreshed = timezone.now() - timedelta(days=7)
        user_auth.save()

        SpotifyAuth.get_and_refresh_spotify_auth_record(user_auth.id)

        mock_refresh_access_token.assert_called_once_with(user_auth.refresh_token)

    def test_get_and_refresh_spotify_user_auth_record_with_missing_record_raises_exception(self):
        invalid_auth_id = 999999

        with self.assertRaises(SpotifyAuth.DoesNotExist):
            SpotifyAuth.get_and_refresh_spotify_auth_record(invalid_auth_id)

    @mock.patch('spotify_client.SpotifyClient.refresh_access_token')
    def test_get_and_refresh_spotify_user_auth_record_raises_spotify_exception(self, mock_refresh_access_token):
        mock_refresh_access_token.side_effect = SpotifyException

        user_auth = MoodyUtil.create_spotify_auth(self.user)
        user_auth.last_refreshed = timezone.now() - timedelta(days=7)
        user_auth.save()

        with self.assertRaises(SpotifyException):
            SpotifyAuth.get_and_refresh_spotify_auth_record(user_auth.id)

    def test_has_scopes_returns_true_for_scope_assigned_to_record(self):
        scope = 'playlist-modify-public'
        user_auth = MoodyUtil.create_spotify_user_auth(self.user)
        user_auth.scopes = [scope]
        user_auth.save()

        self.assertTrue(user_auth.has_scope(scope))

    def test_has_scopes_returns_false_for_scope_not_assigned_to_record(self):
        scope = 'playlist-modify-public'
        desired_scope = 'user-top-read'
        user_auth = MoodyUtil.create_spotify_auth(self.user)
        user_auth.scopes = [scope]
        user_auth.save()

        self.assertFalse(user_auth.has_scope(desired_scope))
