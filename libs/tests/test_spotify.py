from unittest import mock

from django.conf import settings
from django.test import TestCase, override_settings

from requests.exceptions import HTTPError

from libs.spotify import SpotifyClient, SpotifyException


@override_settings(CACHE={'default': settings.CACHES['dummy']})
class TestSpotifyClient(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.spotify_client = SpotifyClient()
        cls.auth_code = 'some-auth-code'

    @override_settings(SPOTIFY={'client_id': 'foo', 'secret_key': 'bar', 'auth_url': 'https://example.com'})
    @mock.patch('libs.spotify.SpotifyClient._make_spotify_request')
    def test_make_auth_access_token_request_happy_path(self, mock_request):
        mock_request.return_value = {'access_token': self.auth_code}

        auth = self.spotify_client._make_auth_access_token_request()

        self.assertEqual(auth, self.auth_code)

    @override_settings(SPOTIFY={'client_id': 'foo', 'secret_key': 'bar', 'auth_url': 'https://example.com'})
    @mock.patch('libs.spotify.SpotifyClient._make_spotify_request')
    def test_make_auth_access_token_request_auth_code_not_found(self, mock_request):
        mock_request.return_value = {}

        auth = self.spotify_client._make_auth_access_token_request()

        self.assertIsNone(auth)

    @mock.patch('django.core.cache.cache.set')
    @mock.patch('django.core.cache.cache.get')
    @mock.patch('libs.spotify.SpotifyClient._make_auth_access_token_request')
    def test_get_auth_token_not_in_cache(self, mock_access_request, mock_cache_get, mock_cache_set):
        mock_cache_get.return_value = None
        mock_access_request.return_value = self.auth_code

        self.spotify_client._get_auth_access_token()
        mock_access_request.assert_called_with()
        mock_cache_set.assert_called_with(
            settings.SPOTIFY['auth_cache_key'],
            self.auth_code,
            settings.SPOTIFY['auth_cache_key_timeout']
        )

    @mock.patch('django.core.cache.cache.get')
    @mock.patch('libs.spotify.SpotifyClient._make_auth_access_token_request')
    def test_get_auth_token_found_in_cache(self, mock_access_request, mock_cache):
        mock_cache.return_value = self.auth_code

        self.spotify_client._get_auth_access_token()
        mock_access_request.assert_not_called()

    @mock.patch('django.core.cache.cache.get')
    @mock.patch('libs.spotify.SpotifyClient._make_auth_access_token_request')
    def test_get_auth_token_fails(self, mock_access_request, mock_cache_get):
        mock_cache_get.return_value = None
        mock_access_request.return_value = None

        with self.assertRaises(SpotifyException):
            self.spotify_client._get_auth_access_token()

    @mock.patch('requests.request')
    @mock.patch('libs.spotify.SpotifyClient._get_auth_access_token')
    def test_spotify_request_happy_path(self, mock_auth, mock_request):
        dummy_response = {'status': 200, 'content': 'OK'}
        dummy_params = {'query': 'param'}
        dummy_data = {'key': 'value'}

        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = None
        mock_response.json.return_value = dummy_response

        mock_auth.return_value = self.auth_code
        mock_request.return_value = mock_response

        self.spotify_client._make_spotify_request('GET', '/dummy_endpoint', data=dummy_data, params=dummy_params)

        mock_request.assert_called_with(
            'GET',
            '/dummy_endpoint',
            params=dummy_params,
            data=dummy_data,
            headers={'Authorization': 'Bearer {}'.format(self.auth_code)}
        )

    @mock.patch('requests.request')
    @mock.patch('libs.spotify.SpotifyClient._get_auth_access_token')
    def test_spotify_request_raises_http_error(self, mock_auth, mock_request):
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = HTTPError

        mock_auth.return_value = self.auth_code
        mock_request.return_value = mock_response

        response = self.spotify_client._make_spotify_request('GET', '/dummy_endpoint')

        self.assertDictEqual(response, {})

    @mock.patch('requests.request')
    @mock.patch('libs.spotify.SpotifyClient._get_auth_access_token')
    def test_spotify_request_raises_base_exception(self, mock_auth, mock_request):
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = Exception

        mock_auth.return_value = self.auth_code
        mock_request.return_value = mock_response

        response = self.spotify_client._make_spotify_request('GET', '/dummy_endpoint')

        self.assertDictEqual(response, {})

    @mock.patch('libs.spotify.SpotifyClient._make_spotify_request')
    def test_get_playlists_for_category_happy_path(self, mock_request):
        mock_request.return_value = {
            'playlists': {
                'items': [{
                    'name': 'Super Dope',
                    'id': 'unique-id',
                    'owner': {
                        'id': 'unique-user-id'
                    },
                }],
            },
        }

        expected_resp = [{
            'name': 'Super Dope'.encode('ascii', 'ignore'),
            'uri': 'unique-id',
            'user': 'unique-user-id'
        }]

        resp = self.spotify_client.get_playlists_for_category('category', 1)

        self.assertEqual(resp, expected_resp)
        mock_request.assert_called_with(
            'GET',
            '{api_url}/browse/categories/{category_id}/playlists'.format(
                api_url=settings.SPOTIFY['api_url'],
                category_id='category'
            ),
            params= {
                'country': settings.COUNTRY_CODE,
                'limit': 1
            }
        )

    @mock.patch('libs.spotify.SpotifyClient._make_spotify_request')
    def test_get_playlist_for_category_raises_exception_if_no_playlists_retrieved(self, mock_request):
        mock_request.return_value = {}

        with self.assertRaises(SpotifyException):
            self.spotify_client.get_playlists_for_category('category', 1)

    @mock.patch('libs.spotify.SpotifyClient._make_spotify_request')
    def test_get_songs_from_playlist_happy_path(self, mock_request):
        mock_playlist = {'user': 'two-tone-killer', 'uri': 'beats-pub'}

        mock_request.return_value = {
            'tracks': {
                'items': [{
                    'track': {
                        'uri': 'song-uri',
                        'explicit': False,
                        'name': 'Glazed',
                        'artists': [{
                            'name': 'J Dilla'
                        }],
                    }
                }]
            }
        }

        expected_return = {
            'name': 'Glazed'.encode('utf-8'),
            'artist': 'J Dilla'.encode('utf-8'),
            'code': 'song-uri'
        }

        actual_return = self.spotify_client.get_songs_from_playlist(mock_playlist, 1)
        self.assertDictEqual(expected_return, actual_return[0])

    @mock.patch('libs.spotify.SpotifyClient._make_spotify_request')
    def test_get_songs_from_playlist_excludes_song_already_seen(self, mock_request):
        self.spotify_client.seen_songs = ['already-seen-code']
        mock_playlist = {'user': 'two-tone-killer', 'uri': 'beats-pub'}

        mock_request.return_value = {
            'tracks': {
                'items': [{
                    'track': {
                        'uri': 'already-seen-code',
                        'explicit': False,
                    }
                }]
            }
        }

        actual_return = self.spotify_client.get_songs_from_playlist(mock_playlist, 1)
        self.assertFalse(actual_return)
        self.spotify_client.seen_songs = []

    @mock.patch('libs.spotify.SpotifyClient._make_spotify_request')
    def test_get_songs_from_playlist_excludes_song_is_explicit(self, mock_request):
        mock_playlist = {'user': 'two-tone-killer', 'uri': 'beats-pub'}

        mock_request.return_value = {
            'tracks': {
                'items': [{
                    'track': {
                        'uri': 'song-uri',
                        'explicit': True,
                    }
                }]
            }
        }

        actual_return = self.spotify_client.get_songs_from_playlist(mock_playlist, 1)
        self.assertFalse(actual_return)

    @mock.patch('libs.spotify.SpotifyClient._make_spotify_request')
    def test_get_songs_from_playlist_handles_empty_tracks(self, mock_request):
        mock_playlist = {'user': 'two-tone-killer', 'uri': 'beats-pub'}

        mock_request.return_value = {
            'tracks': {
                'items': [{
                    'track': None
                }]
            }
        }

        actual_return = self.spotify_client.get_songs_from_playlist(mock_playlist, 1)
        self.assertFalse(actual_return)
