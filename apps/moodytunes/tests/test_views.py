import tempfile
from unittest import mock

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status

from accounts.models import SpotifyUserAuth
from libs.spotify import SpotifyException
from libs.tests.helpers import MoodyUtil, get_messages_from_response
from tunes.models import Emotion


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

    @mock.patch('moodytunes.tasks.FetchSongFromSpotifyTask.delay')
    def test_happy_path(self, mock_task):
        data = {'code': 'spotify:track:2E0Y5LQdiqrPDJJoEyfSqC'}
        self.client.post(self.url, data)

        mock_task.assert_called_once_with('spotify:track:2E0Y5LQdiqrPDJJoEyfSqC', username=self.user.username)

    @mock.patch('moodytunes.tasks.FetchSongFromSpotifyTask.delay')
    def test_task_not_called_for_duplicate_song(self, mock_task):
        song = MoodyUtil.create_song()
        data = {'code': song.code}
        self.client.post(self.url, data)

        mock_task.assert_not_called()

    @mock.patch('moodytunes.tasks.FetchSongFromSpotifyTask.delay')
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
    @mock.patch('moodytunes.tasks.FetchSongFromSpotifyTask.delay', mock.Mock())
    def test_requests_are_rate_limited_after_max_requests_processed(self):
        for _ in range(3):
            data = {'code': MoodyUtil._generate_song_code()}
            self.client.post(self.url, data)

        data = {'code': MoodyUtil._generate_song_code()}
        resp = self.client.post(self.url, data)

        messages = get_messages_from_response(resp)
        last_message = messages[-1]

        self.assertEqual(last_message, 'You have submitted too many suggestions! Try again in a minute')


class TestSpotifyAuthenticationView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.url = reverse('moodytunes:spotify-auth')

    def setUp(self):
        self.client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    @mock.patch('moodytunes.views.get_random_string')
    def test_spotify_oauth_url_is_built_properly(self, mock_random_string):
        random_string = 'foo'
        mock_random_string.return_value = random_string

        expected_auth_url = 'https://accounts.spotify.com/authorize?client_id={client_id}\
        &response_type=code&scope=playlist-modify-public+user-top-read\
        &redirect_uri=https%3A%2F%2Fmoodytunes.vm%2Fmoodytunes%2Fspotify%2Fcallback%2F&state={state}\
        '.format(
            client_id=settings.SPOTIFY['client_id'],
            state=random_string
        )

        resp = self.client.get(self.url)

        self.assertEqual(resp.context['spotify_auth_url'], expected_auth_url.replace(' ', ''))


@mock.patch('accounts.tasks.UpdateTopArtistsFromSpotify.delay', mock.MagicMock)
class TestSpotifyAuthenticationCallbackView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.other_user = MoodyUtil.create_user(username='other_user')
        cls.url = reverse('moodytunes:spotify-auth-callback')
        cls.success_url = reverse('moodytunes:export')
        cls.failure_url = reverse('moodytunes:spotify-auth-failure')
        cls.state = 'state-key'

    def setUp(self):
        self.client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

        session = self.client.session
        session['state'] = self.state
        session.save()

    @mock.patch('moodytunes.views.SpotifyClient')
    def test_happy_path(self, mock_spotify):
        spotify_client = mock.Mock()
        spotify_client.get_access_and_refresh_tokens.return_value = {
            'access_token': 'test-access-token',
            'refresh_token': 'test-refresh-token'
        }

        spotify_client.get_user_profile.return_value = {'id': 'test-user-id'}

        mock_spotify.return_value = spotify_client

        query_params = {'code': 'test-spotify-code', 'state': self.state}

        resp = self.client.get(self.url, data=query_params, follow=True)

        self.assertRedirects(resp, self.success_url)
        self.assertTrue(SpotifyUserAuth.objects.filter(user=self.user).exists())

    def test_error_in_callback_returns_error_page(self):
        query_params = {'error': 'access_denied', 'state': self.state}

        resp = self.client.get(self.url, data=query_params)

        self.assertRedirects(resp, self.failure_url)
        self.assertFalse(SpotifyUserAuth.objects.filter(user=self.user).exists())

    @mock.patch('moodytunes.views.SpotifyClient')
    def test_duplicate_attempts_for_same_moody_user_results_in_success(self, mock_spotify):
        MoodyUtil.create_spotify_user_auth(
            user=self.user,
            access_token='test-access-token',
            refresh_token='test-refresh-token',
            spotify_user_id='test-user-id'
        )

        spotify_client = mock.Mock()
        spotify_client.get_access_and_refresh_tokens.return_value = {
            'access_token': 'test-access-token',
            'refresh_token': 'test-refresh-token'
        }

        spotify_client.get_user_profile.return_value = {'id': 'test-user-id'}

        mock_spotify.return_value = spotify_client

        query_params = {'code': 'test-spotify-code', 'state': self.state}

        resp = self.client.get(self.url, data=query_params, follow=True)

        self.assertRedirects(resp, self.success_url)
        self.assertEqual(SpotifyUserAuth.objects.filter(user=self.user).count(), 1)

    @mock.patch('moodytunes.views.SpotifyClient')
    def test_duplicate_attempts_with_different_moody_users_results_in_failure(self, mock_spotify):
        MoodyUtil.create_spotify_user_auth(
            user=self.other_user,
            access_token='test-access-token',
            refresh_token='test-refresh-token',
            spotify_user_id='test-user-id'
        )

        spotify_client = mock.Mock()
        spotify_client.get_access_and_refresh_tokens.return_value = {
            'access_token': 'test-access-token',
            'refresh_token': 'test-refresh-token'
        }

        spotify_client.get_user_profile.return_value = {'id': 'test-user-id'}

        mock_spotify.return_value = spotify_client

        query_params = {'code': 'test-spotify-code', 'state': self.state}

        resp = self.client.get(self.url, data=query_params, follow=True)

        messages = get_messages_from_response(resp)
        last_message = messages[-1]

        self.assertRedirects(resp, self.failure_url)
        self.assertEqual(last_message, 'Spotify user test-user-id has already authorized MoodyTunes.')

    def test_invalid_state_para_raises_error(self):
        query_params = {'code': 'test-spotify-code', 'state': 'bad-state-value'}

        resp = self.client.get(self.url, data=query_params, follow=True)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('moodytunes.views.SpotifyClient')
    def test_spotify_error_fetching_tokens_redirects_to_error_page(self, mock_spotify):
        spotify_client = mock.Mock()
        spotify_client.get_access_and_refresh_tokens.side_effect = SpotifyException

        mock_spotify.return_value = spotify_client

        query_params = {'code': 'test-spotify-code', 'state': self.state}

        resp = self.client.get(self.url, data=query_params, follow=True)

        messages = get_messages_from_response(resp)
        last_message = messages[-1]

        self.assertRedirects(resp, self.failure_url)
        self.assertEqual(last_message, 'We were unable to retrieve your Spotify profile. Please try again.')

    @mock.patch('moodytunes.views.SpotifyClient')
    def test_spotify_error_fetching_profile_redirects_to_error_page(self, mock_spotify):
        spotify_client = mock.Mock()
        spotify_client.get_access_and_refresh_tokens.return_value = {
            'access_token': 'test-access-token',
            'refresh_token': 'test-refresh-token'
        }

        spotify_client.get_user_profile.side_effect = SpotifyException
        mock_spotify.return_value = spotify_client

        query_params = {'code': 'test-spotify-code', 'state': self.state}

        resp = self.client.get(self.url, data=query_params, follow=True)

        messages = get_messages_from_response(resp)
        last_message = messages[-1]

        self.assertRedirects(resp, self.failure_url)
        self.assertEqual(last_message, 'We were unable to retrieve your Spotify profile. Please try again.')


class TestExportView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.user_with_no_auth = MoodyUtil.create_user(username='no-auth')
        cls.url = reverse('moodytunes:export')

        cls.spotify_auth = MoodyUtil.create_spotify_user_auth(cls.user)

    def setUp(self):
        self.client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    def test_user_with_no_auth_redirect_to_auth_page(self):
        self.client.logout()
        self.client.login(username=self.user_with_no_auth.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)
        resp = self.client.get(self.url)

        self.assertRedirects(resp, reverse('moodytunes:spotify-auth'))

    @mock.patch('moodytunes.tasks.CreateSpotifyPlaylistFromSongsTask.delay')
    def test_post_request_happy_path(self, mock_task_call):
        # Set up playlist for creation
        song = MoodyUtil.create_song()
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        MoodyUtil.create_user_song_vote(self.user, song, emotion, True)

        playlist_name = 'test'
        data = {
            'playlist_name': playlist_name,
            'emotion': emotion.name
        }

        self.client.post(self.url, data)

        mock_task_call.assert_called_once()

    def test_post_request_with_no_user_auth_returns_not_found(self):
        self.client.logout()
        self.client.login(username=self.user_with_no_auth.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

        # Set up playlist for creation
        song = MoodyUtil.create_song()
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        MoodyUtil.create_user_song_vote(self.user_with_no_auth, song, emotion, True)

        playlist_name = 'test'
        data = {
            'playlist_name': playlist_name,
            'emotion': emotion.name
        }

        resp = self.client.post(self.url, data)

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_empty_playlist_displays_error(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)

        playlist_name = 'test'
        data = {
            'playlist_name': playlist_name,
            'emotion': emotion.name
        }

        resp = self.client.post(self.url, data)

        messages = get_messages_from_response(resp)
        last_message = messages[-1]
        msg = 'Your {} playlist is empty! Try adding some songs to save the playlist'.format(
            emotion.full_name.lower()
        )

        self.assertEqual(last_message, msg)

    def test_post_bad_request_displays_error(self):
        playlist_name = 'test'
        data = {
            'playlist_name': playlist_name,
            'emotion': 'bad-value'
        }

        resp = self.client.post(self.url, data)

        messages = get_messages_from_response(resp)
        last_message = messages[-1]
        msg = 'Please submit a valid request'

        self.assertEqual(last_message, msg)
