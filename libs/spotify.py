from base64 import b64encode
import logging
import random

from django.conf import settings
from django.core.cache import cache

import requests
from requests.exceptions import HTTPError

from libs.moody_logging import format_module_name_with_project_prefix

module_name = format_module_name_with_project_prefix(__name__)
logger = logging.getLogger(module_name)


class SpotifyException(Exception):
    """Exception to raise in case something bad happens during request"""
    pass


class SpotifyClient(object):
    """Wrapper around the Spotify API"""
    def __init__(self, command_id=None):
        self._unique_id = command_id

        access_token = cache.get(settings.SPOTIFY_AUTH_CACHE_KEY)

        if not access_token:
            logger.info('{} - Cache miss for auth access token'.format(self._unique_id))
            access_token = self._get_auth_access_token()

            if access_token:
                cache.set(settings.SPOTIFY_AUTH_CACHE_KEY, access_token, settings.SPOTIFY_AUTH_CACHE_TTL)
            else:
                logger.warning('{} - Unable to retrieve access token from Spotify'.format(self._unique_id))

            raise SpotifyException('Unable to retrieve Spotify access token')


        self.access_token = access_token

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
        logger.info('{} - Making {} request to Spotify URL: {}'.format(self._unique_id, method, url))

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

    def get_playlists_for_category(self, category, num_playlists):
        """
        Get a number of playlists from Spotify for a given category
        :param category: Category ID of a genre in Spotify (str)
        :param num_playlists: Number of playlists to return (int)
        @return retrieved_playlists: List of playlist dictionaries for the category
            - name (str): Name of the playlist
            - uri (str): Spotiy ID for the playlist
            - user (str): Spotify ID for the playlist owner
        """
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

            raise SpotifyException('Unable to fetch playlists for {}'.format(category))

        retrieved_playlists = []
        for playlist in response['playlists']['items']:
            payload = {
                'name': playlist['name'].encode('ascii', 'ignore'),
                'uri': playlist['id'],
                'user': playlist['owner']['id']
            }

            retrieved_playlists.append(payload)

        return retrieved_playlists

    def get_songs_from_playlist(self, playlist, num_songs):
        """
        Get a number of songs randomly from the given playlist.
        List of songs is shuffled and the number of desired tracks are returned.
        :param playlist: Mapping of values needed to retrieve playlist tracks (dict)
        :param num_songs: Number of songs to return from this playlist (int)
        @return retrieved_tracks: List of track dictionaries
            - name (str): Name of the song
            - artist (str): Name of the artist
            - uri (str): Spotify ID of the song
        """
        url = '{api_url}/users/{user_id}/playlists/{playlist_id}'.format(
            api_url=settings.SPOTIFY_API_URL,
            user_id=playlist['user'],
            playlist_id=playlist['uri']
        )

        response = self._make_spotify_request(
            'GET',
            url,
        )

        if not response:
            logger.warning('{} - Failed to get songs from playlist {}'.format(self._unique_id, playlist['uri']))

            raise SpotifyException('Unable to fetch songs from playlist {}'.format(playlist['name']))

        processed_tracks = 0
        idx = 0
        retrieved_tracks = []

        tracks = response['tracks']['items']
        random.shuffle(tracks)

        # Process number of tracks requested, but if playlist does not have enough
        # to return the full amount we can return what we get
        while processed_tracks < num_songs and tracks:
            payload = {
                'name': tracks[idx]['track']['name'].encode('ascii','ignore'),
                'artist': tracks[idx]['track']['artists'][0]['name'].encode('ascii','ignore'),
                'uri': tracks[idx]['track']['uri']
            }

            retrieved_tracks.append(payload)
            processed_tracks += 1

            tracks.pop(idx)  # Remove track from list
            idx += 1

        return retrieved_tracks
