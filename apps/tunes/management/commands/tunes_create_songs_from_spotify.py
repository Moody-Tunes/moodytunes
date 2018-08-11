from base64 import b64encode
import logging
import requests
from requests.exceptions import HTTPError

from django.conf import settings
from django.core.management.base import CommandError

from base.management.commands import MoodyBaseCommand
from libs.moody_logging import format_module_name_with_project_prefix

module_name = format_module_name_with_project_prefix(__name__)
logger = logging.getLogger(module_name)


class Command(MoodyBaseCommand):
    """Management command to fetch and create songs from Spotify API"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: Cache this value with a timeout as long as Spotify honours a token for
        self.access_token = self._get_auth_access_token()
        if not self.access_token:
            logger.warning('{} - Unable to retrieve access token from Spotify'.format(self._unique_id))

            raise CommandError('Unable to retrieve Spotify access token')

    def _make_spotify_request(self, method, url, params=None, data=None, headers=None):
        """
        Make a request to the Spotify API and return the JSON response
        :param method: HTTP method to use when sending request (str)
        :param url: URL to send request to (str)
        :param params: GET query params to add to URL (dict)
        :param data: POST data to send in request (dict)
        :param headers: Headers to include in request (dict)
        @return response: Dictionary containg response content
        """
        logger.info('{} - Making {} request to Spotify URL: {}'.format(id=self._unique_id, method=method, url=url))

        if not headers:
            # We have already authenticated, include the `access_token`
            headers = {'Authorization': 'Bearer {}'.format(self.access_token)}

        try:
            response = requests.request(
                method,
                url,
                params=params,
                data=data,
                headers=headers
            )
            response.raise_for_status()
            response = response.json()

        except HTTPError:
            logger.warning('{} - Received HTTPError requesting {}'.format(self._unique_id, url), exc_info=True)
            response = {}

        except Exception:
            logger.error('{} - Received unhandle exception requesting {}'.format(self._unique_id, url), exc_info=True)
            response = {}

        return response

    def _get_auth_access_token(self):
        """
        Get an access token from Spotify for authentication
        @return access_token: Token used for authentication with Spotify (str)
        """
        auth_val = '{client_id}:{secret_key}'.format(
            client_id=settings.SPOTIFY_CLIENT_ID,
            secret_key=settings.SPOTIFY_SECRET_KEY
        )
        auth_val = bytes(auth_val, encoding='utf-8')
        auth_header = b64encode(auth_val)

        headers = {
            'Authorization': 'Basic {}'.format(auth_header.decode('utf8'))
        }

        data = {'grant_type': 'client_credentials'}

        resp = self._make_spotify_request(
            'POST',
            settings.SPOTIFY_AUTH_URL,
            data=data,
            headers=headers
        )

        return resp.get('access_token')

    def _get_playlists_for_category(self, category, num_playlists):
        """
        Get a number of playlists from Spotify for a given category
        :param category: Category ID of a genre in Spotify (str)
        :param num_playlists: Number of playlists to return (int)
        @return playlists: List of playlist dictionaries for the category
            - name (str): Name of the playlist
            - uri (str): Spotiy ID for the playlist
            - user (str): Spotify ID for the playlist owner
        """
        logger.info('{} - Making request to /browse/category for {}'.format(self._unique_id, category))

        url = '{api_url}/browse/categories/{category_id}/playlists'.format(
            api_url=settings.SPOTIFY_API_URL,
            category_id=category
        )

        params = {
            'country': settings.COUNTRY_CODE,
            'limit': num_playlists
        }

        response = self._make_spotify_request(
            'GET',
            url,
            params=params
        )

        if not response:
            logger.warning('{} - Failed to fetch playlists for category {}'.format(self._unique_id, category))

            raise CommandError('Unable to fetch playlists for {}'.format(category))

        retrieved_playlists = []
        for playlist in response['playlists']['items']:
            payload = {
                'name': playlist['name'].encode('ascii', 'ignore'),
                'uri': playlist['id'],
                'user': playlist['owner']['id']
            }

            retrieved_playlists.append(payload)

        return retrieved_playlists

    def handle(self, *args, **options):
        logger.info('{} - Starting run to create songs from Spotify'.format(self._unique_id))

        category = settings.SPOTIFY_CATEGORIES[0]
        num_playlists = 10
        self._get_playlists_for_category(category, num_playlists)
