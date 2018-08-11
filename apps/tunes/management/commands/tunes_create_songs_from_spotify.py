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
        self.access_token = self._get_auth_access_token()
        if not self.access_token:
            logger.warning(
                '{id} - Unable to retrieve access token from Spotify'.format(
                    id=self._unique_id
                )
            )

            raise CommandError('Unable to retrieve Spotify access token')

    def _make_spotify_request(self, method, url, params=None, data=None,
                              headers=None):
        """
        Make a request to the Spotify API and return the JSON response
        :param method: HTTP method to use when sending request (str)
        :param url: URL to send request to (str)
        :param params: GET query params to add to URL (dict)
        :param data: POST data to send in request (dict)
        :param headers: Headers to include in request (dict)
        @return response: Dictionary containg response content
        """
        logger.info(
            '{id} - Making {method} request to Spotify URL: {url}'.format(
                id=self._unique_id,
                method=method,
                url=url
            )
        )

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
            logger.warning(
                '{id} - Received HTTPError requesting {url}'.format(
                    id=self._unique_id,
                    url=url
                ), exc_info=True
            )
            response = {}

        except Exception:
            logger.error(
                '{id} - Received unhandle exception requesting {url}'.format(
                    id=self._unique_id,
                    url=url
                ), exc_info=True
            )
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

    def handle(self, *args, **options):
        pass
