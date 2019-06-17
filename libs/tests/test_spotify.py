from unittest import mock

from base64 import b64encode
from django.conf import settings
from django.test import TestCase

from requests.exceptions import HTTPError

from libs.spotify import SpotifyClient, SpotifyException
from tests.helpers import generate_random_unicode_string


class TestSpotifyClient(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.spotify_client = SpotifyClient()
        cls.auth_code = 'some-auth-code'

    def setUp(self):
        # Clear seen songs cache from SpotifyClient instance
        self.spotify_client.seen_songs = []

    @mock.patch('libs.spotify.SpotifyClient._make_spotify_request')
    def test_make_auth_access_token_request_happy_path(self, mock_request):
        mock_request.return_value = {'access_token': self.auth_code}

        # Calculate encoded auth header expected by Spotify
        auth_val = '{client_id}:{secret_key}'.format(
            client_id='test-spotify-client-id',
            secret_key='test-spotify-secret_key'
        )

        auth_val = bytes(auth_val, encoding='utf-8')
        auth_header = b64encode(auth_val)

        expected_headers = {'Authorization': 'Basic {}'.format(auth_header.decode('utf8'))}
        expected_request_data = {'grant_type': 'client_credentials'}

        auth = self.spotify_client._make_auth_access_token_request()

        mock_request.assert_called_once_with(
            'POST',
            'https://accounts.spotify.com/api/token',
            data=expected_request_data,
            headers=expected_headers
        )
        self.assertEqual(auth, self.auth_code)

    @mock.patch('libs.spotify.SpotifyClient._make_spotify_request')
    def test_make_auth_access_token_request_auth_code_not_found(self, mock_request):
        mock_request.return_value = {}

        auth = self.spotify_client._make_auth_access_token_request()

        self.assertIsNone(auth)

    @mock.patch('django.core.cache.cache.set')
    @mock.patch('django.core.cache.cache.get')
    @mock.patch('libs.spotify.SpotifyClient._make_auth_access_token_request')
    def test_get_auth_token_not_in_cache_returns_token(self, mock_access_request, mock_cache_get, mock_cache_set):
        mock_cache_get.return_value = None
        mock_access_request.return_value = self.auth_code

        code = self.spotify_client._get_auth_access_token()

        mock_access_request.assert_called_once_with()
        mock_cache_set.assert_called_once_with(
            settings.SPOTIFY['auth_cache_key'],
            self.auth_code,
            settings.SPOTIFY['auth_cache_key_timeout']
        )
        self.assertEqual(code, self.auth_code)

    @mock.patch('django.core.cache.cache.get')
    @mock.patch('libs.spotify.SpotifyClient._make_auth_access_token_request')
    def test_get_auth_token_found_in_cache_returns_token(self, mock_access_request, mock_cache):
        mock_cache.return_value = self.auth_code

        code = self.spotify_client._get_auth_access_token()

        mock_access_request.assert_not_called()
        self.assertEqual(code, self.auth_code)

    @mock.patch('django.core.cache.cache.get')
    @mock.patch('libs.spotify.SpotifyClient._make_auth_access_token_request')
    def test_get_auth_token_raises_spotify_exception_on_failure(self, mock_access_request, mock_cache_get):
        mock_cache_get.return_value = None
        mock_access_request.return_value = None

        with self.assertRaises(SpotifyException):
            self.spotify_client._get_auth_access_token()

    @mock.patch('requests.request')
    @mock.patch('libs.spotify.SpotifyClient._get_auth_access_token')
    def test_make_spotify_request_happy_path(self, mock_auth, mock_request):
        dummy_response = {'status': 200, 'content': 'OK'}
        dummy_params = {'query': 'param'}
        dummy_data = {'key': 'value'}

        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = None
        mock_response.json.return_value = dummy_response

        mock_auth.return_value = self.auth_code
        mock_request.return_value = mock_response

        resp = self.spotify_client._make_spotify_request('GET', '/dummy_endpoint', data=dummy_data, params=dummy_params)

        mock_request.assert_called_with(
            'GET',
            '/dummy_endpoint',
            params=dummy_params,
            data=dummy_data,
            headers={'Authorization': 'Bearer {}'.format(self.auth_code)}
        )
        self.assertDictEqual(resp, dummy_response)

    @mock.patch('requests.request')
    @mock.patch('libs.spotify.SpotifyClient._get_auth_access_token')
    def test_make_spotify_request_raises_spotify_exception_on_http_error(self, mock_auth, mock_request):
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = HTTPError

        mock_auth.return_value = self.auth_code
        mock_request.return_value = mock_response

        with self.assertRaises(SpotifyException):
            self.spotify_client._make_spotify_request('GET', '/dummy_endpoint')

    @mock.patch('requests.request')
    @mock.patch('libs.spotify.SpotifyClient._get_auth_access_token')
    def test_make_spotify_request_raises_spotify_exception_on_base_exception(self, mock_auth, mock_request):
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = Exception

        mock_auth.return_value = self.auth_code
        mock_request.return_value = mock_response

        with self.assertRaises(SpotifyException):
            self.spotify_client._make_spotify_request('GET', '/dummy_endpoint')

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
            params={
                'country': settings.COUNTRY_CODE,
                'limit': 1
            }
        )

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
    def test_get_songs_from_playlist_with_unicode_data(self, mock_request):
        mock_playlist = {'user': 'two-tone-killer', 'uri': 'beats-pub'}
        song_name = generate_random_unicode_string(10)
        song_artist = generate_random_unicode_string(10)

        mock_request.return_value = {
            'tracks': {
                'items': [{
                    'track': {
                        'uri': 'song-uri',
                        'explicit': False,
                        'name': song_name,
                        'artists': [{
                            'name': song_artist
                        }],
                    }
                }]
            }
        }

        expected_return = {
            'name': song_name.encode('utf-8'),
            'artist': song_artist.encode('utf-8'),
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

    @mock.patch('libs.spotify.SpotifyClient._make_spotify_request')
    def test_get_song_from_playlist_respects_limit(self, mock_request):
        mock_playlist = {'user': 'two-tone-killer', 'uri': 'beats-pub'}

        mock_request.return_value = {
            'tracks': {
                'items': [
                    {
                        'track': {
                            'uri': 'song-uri',
                            'explicit': False,
                            'name': 'Glazed',
                            'artists': [{
                                'name': 'J Dilla'
                            }],
                        },
                    },
                    {
                        'track': {
                            'uri': 'other-song-uri',
                            'explicit': False,
                            'name': 'King',
                            'artists': [{
                                'name': 'J Dilla'
                            }],
                        },
                    },
                ]
            }
        }

        resp = self.spotify_client.get_songs_from_playlist(mock_playlist, 1)
        self.assertEqual(len(resp), 1)

    @mock.patch('libs.spotify.SpotifyClient._make_spotify_request')
    def test_get_audio_features_for_tracks_happy_path(self, mock_request):
        track = {'code': 'spotify:song:code'}
        tracks = [track]

        mock_request.return_value = {
            'audio_features': [{
                'valence': .5,
                'energy': .5
            }]
        }

        resp = self.spotify_client.get_audio_features_for_tracks(tracks)
        new_track = resp[0]

        self.assertEqual(new_track['energy'], .5)
        self.assertEqual(new_track['valence'], .5)

    @mock.patch('libs.spotify.SpotifyClient._make_spotify_request')
    def test_get_audio_features_handles_missing_track_data(self, mock_request):
        track = {'code': 'spotify:song:code'}
        tracks = [track]

        mock_request.return_value = {
            'audio_features': [{}]
        }

        resp = self.spotify_client.get_audio_features_for_tracks(tracks)
        new_track = resp[0]

        self.assertIsNone(new_track.get('energy'))
        self.assertIsNone(new_track.get('valence'))

    @mock.patch('libs.spotify.SpotifyClient._make_spotify_request')
    def test_get_audio_features_for_tracks_skips_tracks_missing_features(self, mock_request):
        track = {'code': 'spotify:song:code'}
        tracks = [track]

        mock_request.return_value = {
            'audio_features': [{
                'valence': .5,
            }]
        }

        resp = self.spotify_client.get_audio_features_for_tracks(tracks)
        new_track = resp[0]

        self.assertIsNone(new_track.get('energy'))
        self.assertIsNone(new_track.get('valence'))

    @mock.patch('libs.spotify.SpotifyClient._make_spotify_request')
    def test_get_user_tokens(self, mock_request):
        request_data = {
            'code': 'some-code',
            'redirect_uri': 'redirect/uri',
        }
        resp_data = {
            'access_token': 'some:access:token',
            'refresh_token': 'some:refresh:token'
        }

        mock_request.return_value = resp_data

        user_tokens = self.spotify_client.get_access_and_refresh_tokens(**request_data)

        request_data.update({'grant_type': 'authorization_code'})  # Update with constant grant_type from Spotify
        mock_request.assert_called_once_with(
            'POST',
            'https://accounts.spotify.com/api/token',
            data=request_data
        )
        self.assertDictEqual(user_tokens, resp_data)

    @mock.patch('libs.spotify.SpotifyClient._make_spotify_request')
    def test_refresh_access_token(self, mock_request):
        request_data = {'refresh_token': 'some:refresh:token'}
        resp_data = {'access_token': 'some:access:token'}
        mock_request.return_value = resp_data

        access_token = self.spotify_client.refresh_access_token(**request_data)

        request_data.update({'grant_type': 'refresh_token'})  # Update with constant grant_type from Spotify
        mock_request.assert_called_once_with(
            'POST',
            'https://accounts.spotify.com/api/token',
            data=request_data
        )
        self.assertEqual(access_token, resp_data['access_token'])
