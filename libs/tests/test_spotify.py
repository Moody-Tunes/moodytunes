from unittest import mock

from django.conf import settings
from django.test import TestCase, override_settings

from requests.exceptions import HTTPError

from libs.spotify import SpotifyClient


@override_settings(CACHE={'default': settings.CACHES['dummy']})
class TestSpotifyClient(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.spotify_client = SpotifyClient()
        cls.auth_code = 'some-auth-code'

    @mock.patch('django.core.cache.cache.get')
    @mock.patch('libs.spotify.SpotifyClient._make_auth_access_token_request')
    def test_get_auth_token_not_in_cache(self, mock_access_request, mock_cache):
        mock_cache.return_value = None
        mock_access_request.return_value = self.auth_code

        self.spotify_client._get_auth_access_token()
        mock_access_request.assert_called_with()

    @mock.patch('django.core.cache.cache.get')
    @mock.patch('libs.spotify.SpotifyClient._make_auth_access_token_request')
    def test_get_auth_token_found_in_cache(self, mock_access_request, mock_cache):
        mock_cache.return_value = self.auth_code

        self.spotify_client._get_auth_access_token()
        mock_access_request.assert_not_called()

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
