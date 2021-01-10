import os
from io import BytesIO
from unittest import mock

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from spotify_client.exceptions import SpotifyException

from libs.tests.helpers import MoodyUtil, get_messages_from_response
from spotify.models import SpotifyAuth, SpotifyUserData
from tunes.models import Emotion


class TestSpotifyAuthenticationView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.url = reverse('spotify:spotify-auth')

    def setUp(self):
        self.client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    @mock.patch('spotify.views.get_random_string')
    def test_spotify_oauth_url_is_built_properly(self, mock_random_string):
        random_string = 'foo'
        mock_random_string.return_value = random_string

        expected_auth_url = 'https://accounts.spotify.com/authorize?client_id={client_id}\
        &response_type=code&scope=playlist-modify-public+user-top-read+ugc-image-upload\
        &redirect_uri=https%3A%2F%2Fmoodytunes.vm%2Fmoodytunes%2Fspotify%2Fcallback%2F&state={state}\
        '.format(
            client_id=settings.SPOTIFY['client_id'],
            state=random_string
        )

        resp = self.client.get(self.url)

        self.assertEqual(resp.context['spotify_auth_url'], expected_auth_url.replace(' ', ''))


@mock.patch('spotify.tasks.UpdateTopArtistsFromSpotifyTask.delay', mock.MagicMock)
class TestSpotifyAuthenticationCallbackView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.other_user = MoodyUtil.create_user(username='other_user')
        cls.url = reverse('spotify:spotify-auth-callback')
        cls.success_url = reverse('spotify:export')
        cls.failure_url = reverse('spotify:spotify-auth-failure')
        cls.state = 'state-key'

    def setUp(self):
        self.client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

        session = self.client.session
        session['state'] = self.state
        session.save()

    @mock.patch('spotify.views.SpotifyClient')
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
        self.assertTrue(SpotifyAuth.objects.filter(user=self.user).exists())

        auth = SpotifyAuth.objects.get(user=self.user)
        self.assertListEqual(auth.scopes, settings.SPOTIFY['auth_user_scopes'])

    @mock.patch('spotify.views.SpotifyClient')
    def test_success_redirects_to_supplied_redirect(self, mock_spotify):
        redirect_url = reverse('accounts:profile')
        spotify_client = mock.Mock()
        spotify_client.get_access_and_refresh_tokens.return_value = {
            'access_token': 'test-access-token',
            'refresh_token': 'test-refresh-token'
        }

        spotify_client.get_user_profile.return_value = {'id': 'test-user-id'}

        mock_spotify.return_value = spotify_client

        query_params = {'code': 'test-spotify-code', 'state': self.state}

        session = self.client.session
        session['redirect_url'] = redirect_url
        session.save()

        resp = self.client.get(self.url, data=query_params, follow=True)

        self.assertRedirects(resp, redirect_url)

    def test_error_in_callback_returns_error_page(self):
        query_params = {'error': 'access_denied', 'state': self.state}

        resp = self.client.get(self.url, data=query_params)

        self.assertRedirects(resp, self.failure_url)
        self.assertFalse(SpotifyAuth.objects.filter(user=self.user).exists())

    @mock.patch('spotify.views.SpotifyClient')
    def test_duplicate_attempts_for_same_moody_user_results_in_success(self, mock_spotify):
        MoodyUtil.create_spotify_auth(
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
        self.assertEqual(SpotifyAuth.objects.filter(user=self.user).count(), 1)

    @mock.patch('spotify.views.SpotifyClient')
    def test_duplicate_attempts_with_different_moody_users_results_in_failure(self, mock_spotify):
        MoodyUtil.create_spotify_auth(
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

    @mock.patch('spotify.views.SpotifyClient')
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

    @mock.patch('spotify.views.SpotifyClient')
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


class TestRevokeSpotifyAuthView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_without_auth = MoodyUtil.create_user(username='user-no-auth')
        cls.user_with_auth = MoodyUtil.create_user(username='user-with-auth')
        cls.url = reverse('spotify:spotify-auth-revoke')
        cls.redirect_url = reverse('accounts:profile')

    def test_get_request_for_user_without_auth_is_redirected_to_profile_page(self):
        self.client.login(username=self.user_without_auth.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)
        resp = self.client.get(self.url)

        messages = get_messages_from_response(resp)
        last_message = messages[-1]

        self.assertRedirects(resp, self.redirect_url)
        self.assertEqual(last_message, 'You have not authorized MoodyTunes with Spotify')

    def test_post_request_for_user_without_auth_is_redirected_to_profile_page(self):
        self.client.login(username=self.user_without_auth.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)
        resp = self.client.post(self.url)

        messages = get_messages_from_response(resp)
        last_message = messages[-1]

        self.assertRedirects(resp, self.redirect_url)
        self.assertEqual(last_message, 'You have not authorized MoodyTunes with Spotify')

    def test_get_request_for_user_with_auth_displays_revoke_page(self):
        MoodyUtil.create_spotify_auth(self.user_with_auth)
        self.client.login(username=self.user_with_auth.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(resp, 'spotify/revoke_spotify_auth.html')

    def test_post_request_for_user_with_auth_deletes_spotify_data(self):
        MoodyUtil.create_spotify_auth(self.user_with_auth)
        self.client.login(username=self.user_with_auth.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

        resp = self.client.post(self.url)

        self.assertFalse(SpotifyAuth.objects.filter(user=self.user_with_auth).exists())
        self.assertFalse(SpotifyUserData.objects.filter(spotify_auth__user=self.user_with_auth).exists())

        messages = get_messages_from_response(resp)
        last_message = messages[-1]

        self.assertRedirects(resp, self.redirect_url)
        self.assertEqual(last_message, 'We have deleted your Spotify data from Moodytunes')


class TestExportView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.user_with_no_auth = MoodyUtil.create_user(username='no-auth')
        cls.url = reverse('spotify:export')

        cls.spotify_auth = MoodyUtil.create_spotify_auth(cls.user)

    def setUp(self):
        self.client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    def test_get_user_with_no_auth_redirect_to_auth_page(self):
        self.client.logout()
        self.client.login(username=self.user_with_no_auth.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)
        resp = self.client.get(self.url)

        self.assertRedirects(resp, reverse('spotify:spotify-auth'))

    def test_get_auth_without_proper_scope_is_redirected_to_auth_page(self):
        # Clear Spotify OAuth scopes for SpotifyUserAuth record
        self.spotify_auth.scopes = []
        self.spotify_auth.save()

        resp = self.client.get(self.url)

        self.assertRedirects(resp, reverse('spotify:spotify-auth'))
        self.assertFalse(SpotifyAuth.objects.filter(user=self.user).exists())

    @mock.patch('spotify.tasks.ExportSpotifyPlaylistFromSongsTask.delay')
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
        msg = 'Your {} playlist is empty! Try adding some songs to export the playlist'.format(
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

    @mock.patch('spotify.tasks.ExportSpotifyPlaylistFromSongsTask.delay')
    def test_post_with_image_upload_saves_image(self, mock_task_call):
        song = MoodyUtil.create_song()
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        MoodyUtil.create_user_song_vote(self.user, song, emotion, True)

        with open('{}/apps/spotify/tests/fixtures/cat.jpg'.format(settings.BASE_DIR), 'rb') as img_file:
            img = BytesIO(img_file.read())
            img.name = 'my_cover.jpg'

        playlist_name = 'test'
        data = {
            'playlist_name': playlist_name,
            'emotion': emotion.name,
            'cover_image': img
        }

        expected_image_filename = '{}/{}_{}_{}.jpg'.format(
            settings.IMAGE_FILE_UPLOAD_PATH,
            self.user.username,
            data['emotion'],
            data['playlist_name'],
        )

        # Cleanup old cover file if exists
        if os.path.exists(expected_image_filename):
            os.unlink(expected_image_filename)

        self.client.post(self.url, data)

        self.assertTrue(os.path.exists(expected_image_filename))

        mock_task_call.assert_called_once_with(
            self.spotify_auth.pk,
            playlist_name,
            [song.code],
            expected_image_filename
        )

    def test_post_with_invalid_image_upload_displays_error(self):
        song = MoodyUtil.create_song()
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        MoodyUtil.create_user_song_vote(self.user, song, emotion, True)

        with open('{}/apps/spotify/tests/fixtures/hack.php'.format(settings.BASE_DIR), 'rb') as hack_file:
            hack = BytesIO(hack_file.read())
            hack.name = 'hack.php'

        playlist_name = 'test'
        data = {
            'playlist_name': playlist_name,
            'emotion': emotion.name,
            'cover_image': hack
        }

        resp = self.client.post(self.url, data)

        messages = get_messages_from_response(resp)
        last_message = messages[-1]
        msg = 'Please submit a valid request'

        self.assertEqual(last_message, msg)


class TestSuggestSongView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.url = reverse('spotify:suggest')

    def setUp(self):
        self.client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    @mock.patch('spotify.tasks.FetchSongFromSpotifyTask.delay')
    def test_happy_path(self, mock_task):
        data = {'code': 'spotify:track:2E0Y5LQdiqrPDJJoEyfSqC'}
        self.client.post(self.url, data)

        mock_task.assert_called_once_with('spotify:track:2E0Y5LQdiqrPDJJoEyfSqC', username=self.user.username)

    @mock.patch('spotify.tasks.FetchSongFromSpotifyTask.delay')
    def test_task_not_called_for_duplicate_song(self, mock_task):
        song = MoodyUtil.create_song()
        data = {'code': song.code}
        self.client.post(self.url, data)

        mock_task.assert_not_called()

    @mock.patch('spotify.tasks.FetchSongFromSpotifyTask.delay')
    def test_task_not_called_for_invalid_code(self, mock_task):
        data = {'code': 'foo'}
        self.client.post(self.url, data)

        mock_task.assert_not_called()

    @mock.patch('ratelimit.decorators.is_ratelimited')
    @mock.patch('spotify.tasks.FetchSongFromSpotifyTask.delay', mock.Mock())
    def test_requests_are_rate_limited_after_max_requests_processed(self, mock_is_ratelimited):
        mock_is_ratelimited.return_value = True

        data = {'code': MoodyUtil._generate_song_code()}
        resp = self.client.post(self.url, data)

        messages = get_messages_from_response(resp)
        last_message = messages[-1]

        self.assertEqual(last_message, 'You have submitted too many suggestions! Try again in a minute')
