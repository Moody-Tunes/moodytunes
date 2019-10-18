import tempfile
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import SpotifyUserAuth
from libs.tests.helpers import MoodyUtil, get_messages_from_response


class TestBrowsePlaylistsView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.url = reverse('moodytunes:browse')

    def setUp(self):
        self.client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    @mock.patch('tunes.utils.CachedPlaylistManager.retrieve_cached_browse_playlist')
    def test_cached_playlist_exists_is_true_in_context(self, mock_cache_retrieve):
        song = MoodyUtil.create_song()
        mock_cache_retrieve.return_value = [song]

        resp = self.client.get(self.url)
        self.assertTrue(resp.context['cached_playlist_exists'])

    @mock.patch('tunes.utils.CachedPlaylistManager.retrieve_cached_browse_playlist')
    def test_cached_playlist_exists_is_false_in_context(self, mock_cache_retrieve):
        mock_cache_retrieve.return_value = None

        resp = self.client.get(self.url)
        self.assertFalse(resp.context['cached_playlist_exists'])


class TestSuggestSongView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.url = reverse('moodytunes:suggest')

    def setUp(self):
        self.client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    @mock.patch('moodytunes.tasks.fetch_song_from_spotify.delay')
    def test_happy_path(self, mock_task):
        data = {'code': 'spotify:track:2E0Y5LQdiqrPDJJoEyfSqC'}
        self.client.post(self.url, data)

        mock_task.assert_called_once_with('spotify:track:2E0Y5LQdiqrPDJJoEyfSqC', username=self.user.username)

    @mock.patch('moodytunes.tasks.fetch_song_from_spotify.delay')
    def test_task_not_called_for_duplicate_song(self, mock_task):
        song = MoodyUtil.create_song()
        data = {'code': song.code}
        self.client.post(self.url, data)

        mock_task.assert_not_called()

    @mock.patch('moodytunes.tasks.fetch_song_from_spotify.delay')
    def test_task_not_called_for_invalid_code(self, mock_task):
        data = {'code': 'foo'}
        self.client.post(self.url, data)

        mock_task.assert_not_called()

    # django-ratelimit relies on cache, so we need to use some temporary cache system for tracking requests
    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': '{}/mtdj_cache'.format(tempfile.gettempdir())
        }
    })
    @mock.patch('moodytunes.tasks.fetch_song_from_spotify.delay', mock.Mock())
    def test_requests_are_rate_limited_after_max_requests_processed(self):
        for _ in range(3):
            data = {'code': MoodyUtil._generate_song_code()}
            self.client.post(self.url, data)

        data = {'code': MoodyUtil._generate_song_code()}
        resp = self.client.post(self.url, data)

        messages = get_messages_from_response(resp)
        last_message = messages[-1]

        self.assertEqual(last_message, 'You have submitted too many suggestions! Try again in a minute')


class TestSpotifyAuthenticationCallbackView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.url = reverse('moodytunes:spotify-auth-callback')
        cls.success_url = reverse('moodytunes:spotify-auth-success')
        cls.failure_url = reverse('moodytunes:spotify-auth-failure')

    def setUp(self):
        self.client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    @mock.patch('moodytunes.views.SpotifyClient')
    def test_happy_path(self, mock_spotify):
        spotify_client = mock.Mock()
        spotify_client.get_access_and_refresh_tokens.return_value = {
            'access_token': 'test-access-token',
            'refresh_token': 'test-refresh-token'
        }

        spotify_client.get_user_profile.return_value = {'id': 'test-user-id'}

        mock_spotify.return_value = spotify_client

        query_params = {'code': 'test-spotify-code'}
        resp = self.client.get(self.url, data=query_params)

        self.assertRedirects(resp, self.success_url)
        self.assertTrue(SpotifyUserAuth.objects.filter(user=self.user).exists())

    def test_error_in_callback_returns_error_page(self):
        query_params = {'error': 'access_denied'}
        resp = self.client.get(self.url, data=query_params)

        self.assertRedirects(resp, self.failure_url)
        self.assertFalse(SpotifyUserAuth.objects.filter(user=self.user).exists())
