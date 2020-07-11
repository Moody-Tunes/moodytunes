import copy
import json
import logging
import random
from base64 import b64encode
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.core.cache import cache


logger = logging.getLogger(__name__)


class SpotifyException(Exception):
    """Exception to raise in case something bad happens during request"""
    pass


class ClientException(Exception):
    """Exception to raise in case of error on our end for request"""


class SpotifyClient(object):
    """Wrapper around the Spotify API"""
    BATCH_SIZE = 100

    REDACT_VALUE = '**********'
    REDACT_DATA_KEYS = ['Authorization', 'code', 'refresh_token', 'access_token']

    def __init__(self, identifier='SpotifyClient'):
        self.fingerprint = identifier
        self.seen_songs = []

    def _sanitize_log_data(self, data):
        """
        Redact sensitive data (auth headers, access tokens, etc.) from logging data and
        replace with a sanitized value.

        :param data: (dict) Request data to log that may contain sensitive information

        :return: (dict)
        """
        for name in data:
            if name in self.REDACT_DATA_KEYS:
                data[name] = self.REDACT_VALUE

        return data

    def _log(self, level, msg, extra=None, exc_info=False):
        """
        Log a message to the logger at a given level with optional extra info or traceback info.

        NOTE: Any data passed as `extra` should be a copy of the real data used in the code. This
        is because we do transformations on the data passed to sanitize sensitive values, so if we
        operate on the "real data" we could inadvertently update the actual data being used in the
        code.

        :param level: (int) Logging level to log at. Should be a constant from the `logging` library
        :param msg: (str) Log message to write to write
        :param extra: (dict) Optional payload of extra logging information
        :param exc_info: (bool) Include traceback information with log message
        """
        if extra is None:
            extra = {}

        extra.update({'fingerprint': self.fingerprint})

        # Redact sensitive information from logging data extra
        for key, data in extra.items():
            if isinstance(data, dict):
                extra[key] = self._sanitize_log_data(data)

        logger.log(level, msg, extra=extra, exc_info=exc_info)

    def _make_spotify_request(self, method, url, params=None, data=None, headers=None):
        """
        Make a request to the Spotify API and return the JSON response

        :param method: (str) HTTP method to use when sending request
        :param url: (str) URL to send request to
        :param params: (dict) GET query params to add to URL
        :param data: (dict) POST data to send in request
        :param headers: (dict) Headers to include in request

        :return (dict) Response content

        :raises: `SpotifyException` if request was unsuccessful
        :raises: `ClientException` if unexpected error encountered
        """

        if not headers:
            # Retrieve the header we need to make an auth request
            auth_token = self._get_auth_access_token()
            headers = {'Authorization': 'Bearer {}'.format(auth_token)}

        logging_params = copy.deepcopy(params)
        logging_data = copy.deepcopy(data)
        logging_headers = copy.deepcopy(headers)

        self._log(
            logging.INFO,
            'Making {method} request to Spotify URL: {url}'.format(
                method=method,
                url=url,
            ),
            extra={
                'request_method': method,
                'params': logging_params,
                'data': logging_data,
                'headers': logging_headers
            }
        )

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

            self._log(logging.INFO, 'Successful request made to {}.'.format(url))
            self._log(
                logging.DEBUG,
                'Successful request made to {}.'.format(url),
                extra={'response_data': copy.deepcopy(response)}
            )

            return response

        except requests.exceptions.HTTPError as exc:
            response = exc.response

            self._log(
                logging.ERROR,
                'Received HTTPError requesting {}'.format(url),
                extra={
                    'request_method': method,
                    'data': logging_data,
                    'params': logging_params,
                    'headers': logging_headers,
                    'response_code': response.status_code,
                    'response_reason': response.reason,
                    'response_data': response.json(),
                },
                exc_info=True
            )

            raise SpotifyException('Received HTTP Error requesting {}'.format(url))

        except Exception:
            self._log(logging.ERROR, 'Received unhandled exception requesting {}'.format(url), exc_info=True)

            raise ClientException('Received unhandled exception requesting {}'.format(url))

    def _get_auth_access_token(self):
        """
        Return the access token we need to make requests to Spotify. Will either hit the cache for the key,
        or make a request to Spotify if the token in the cache is invalid

        :return: (str) Key needed to authenticate with Spotify API

        :raises: `SpotifyException` if access token not retrieved
        """
        access_token = cache.get(settings.SPOTIFY['auth_cache_key'])

        if not access_token:
            self._log(logging.INFO, 'Cache miss for auth access token')
            access_token = self._make_auth_access_token_request()

            if access_token:
                cache.set(settings.SPOTIFY['auth_cache_key'], access_token, settings.SPOTIFY['auth_cache_key_timeout'])
            else:
                self._log(logging.ERROR, 'Unable to retrieve access token from Spotify')

                raise SpotifyException('Unable to retrieve Spotify access token')

        return access_token

    def _make_authorization_header(self):
        """
        Build the Basic Authorization header used for Spotify API authentication

        :return: (str) Base 64 encoded string that contains the client ID and client secret key for application
        """
        auth_val = '{client_id}:{secret_key}'.format(
            client_id=settings.SPOTIFY['client_id'],
            secret_key=settings.SPOTIFY['secret_key']
        )
        auth_val = bytes(auth_val, encoding='utf-8')
        auth_header = b64encode(auth_val)

        return {'Authorization': 'Basic {}'.format(auth_header.decode('utf8'))}

    def _make_auth_access_token_request(self):
        """
        Get an access token from Spotify for authentication

        :return: (str) Token used for authentication with Spotify
        """
        headers = self._make_authorization_header()

        data = {'grant_type': 'client_credentials'}

        resp = self._make_spotify_request(
            'POST',
            settings.SPOTIFY['auth_url'],
            data=data,
            headers=headers
        )

        return resp.get('access_token')

    def get_code_from_spotify_uri(self, code):
        """
        Get the Spotify code (alphanumeric value) from the Spotify song URI. Used in requests to Spotify
        for a track, as Spotify only cares about the alphanumeric value.

        Ex. Given 'spotify:track:19p0PEnGr6XtRqCYEI8Ucc', return '19p0PEnGr6XtRqCYEI8Ucc'

        :param code: (str) Full Spotify URI for a song

        :return: (str) Spotify code for the song
        """
        return code.split(':')[2]

    def batch_tracks(self, tracks, batch_size=None):
        """
        Some Spotify endpoints have a limit on the number of tracks to send in one request. This method will
        take a list of tracks and create a list of batches for including in Spotify requests.

        :param tracks: (list) List of tracks to batch
        :param batch_size: (int) Optional size of batches to return

        :return: (list[list]) Original list of tracks, batched into lists of `batch_size`
        """
        batch_size = batch_size or self.BATCH_SIZE

        return [tracks[idx:idx + batch_size] for idx in range(0, len(tracks), batch_size)]

    def get_playlists_for_category(self, category, num_playlists):
        """
        Get a number of playlists from Spotify for a given category

        :param category: (str) Category ID of a genre in Spotify
        :param num_playlists: (int) Number of playlists to return

        :return: (list[dict]) Playlist mappings for the given category
            - name (str): Name of the playlist
            - uri (str): Spotify ID for the playlist
            - user (str): Spotify ID for the playlist owner
        """
        url = '{api_url}/browse/categories/{category_id}/playlists'.format(
            api_url=settings.SPOTIFY['api_url'],
            category_id=category
        )

        params = {
            'country': settings.COUNTRY_CODE,
            'limit': num_playlists
        }

        response = self._make_spotify_request('GET', url, params=params)

        retrieved_playlists = []
        for playlist in response['playlists']['items']:
            payload = {
                'name': playlist['name'].encode('ascii', 'ignore'),
                'uri': playlist['id'],
                'user': playlist['owner']['id']
            }

            retrieved_playlists.append(payload)

        # Shuffle playlists to ensure freshness
        random.shuffle(retrieved_playlists)

        return retrieved_playlists

    def get_songs_from_playlist(self, playlist, num_songs):
        """
        Get a number of songs randomly from the given playlist.
        List of songs is shuffled and the number of desired tracks are returned.
        :param playlist: (dict) Mapping of values needed to retrieve playlist tracks
        :param num_songs: (int) Number of songs to return from this playlist

        :return: (list[dict]) Song mappings from the given playlist
            - name (str): Name of the song
            - artist (str): Name of the artist
            - code (str): Spotify ID of the song
        """
        url = '{api_url}/users/{user_id}/playlists/{playlist_id}'.format(
            api_url=settings.SPOTIFY['api_url'],
            user_id=playlist['user'],
            playlist_id=playlist['uri']
        )

        params = {'fields': 'tracks(items(track(id,uri,name,artists,explicit)))'}

        response = self._make_spotify_request('GET', url, params=params)

        processed_tracks = 0
        retrieved_tracks = []

        tracks = response['tracks']['items']

        # Shuffle tracks to ensure freshness
        random.shuffle(tracks)

        # Process number of tracks requested, but if playlist does not have enough to return the full
        # amount we return what we get
        # Skip tracks that have already been seen or have explicit lyrics (I want my Mom to use this site)
        for track in tracks:
            if not track['track']:
                # Sometimes Spotify doesn't return anything for a track. Unsure why, but if the track is None
                # we should just skip it and keep going
                continue

            uri = track['track']['uri']
            is_explicit = track['track']['explicit']

            if uri in self.seen_songs or is_explicit:
                continue

            payload = {
                'name': track['track']['name'],
                'artist': track['track']['artists'][0]['name'],
                'code': uri
            }

            retrieved_tracks.append(payload)
            self.seen_songs.append(uri)
            processed_tracks += 1

            if processed_tracks >= num_songs:
                break

        return retrieved_tracks

    def get_audio_features_for_tracks(self, tracks):
        """
        Get audio features (attributes we use for determining song emotion) for a number of tracks. Will update the
        tracks in place, each track in the list is a dictionary of values needed to create a Song object. This method
        returns the list of tracks updated with the tracks emotion attribute values.

        :param tracks: (list[dict]) Song mappings

        :return: (list[dict]) Song mappings + (energy, valence, danceability)
        """
        # Need to batch tracks as Spotify limits the number of tracks sent in one request
        batched_tracks = self.batch_tracks(tracks)

        for batch in batched_tracks:
            url = '{api_url}/audio-features'.format(
                api_url=settings.SPOTIFY['api_url']
            )

            # Construct query params list from track ids in batch
            # Strip spotify:track: from the uri (Spotify just wants the id)
            track_ids = [self.get_code_from_spotify_uri(track['code']) for track in batch]
            params = {'ids': ','.join([track_id for track_id in track_ids])}

            response = self._make_spotify_request('GET', url, params=params)

            # Response is returned in the order requested (req:[1,2,3] -> res:[1,2,3])
            # If an object is not found, a null value is returned in the appropriate position
            for track, track_data in zip(batch, response['audio_features']):
                if track_data:
                    valence = track_data.get('valence')
                    energy = track_data.get('energy')
                    danceability = track_data.get('danceability')

                    # Skip tracks that are missing any of the attributes we're looking for
                    if not any([valence, energy, danceability]):
                        continue

                    track.update({
                        'valence': valence,
                        'energy': energy,
                        'danceability': danceability
                    })

        return tracks

    @staticmethod
    def build_spotify_oauth_confirm_link(state):
        """
        First step in the Spotify user authorization flow. This builds the request to authorize the application with
        Spotify. Note that this function simply builds the URL for the user to visit, the actual behavior for the
        authorization need to be made client-side.

        :param state: (str) State to pass in request. Used for validating redirect URI against request

        :return: (str) URL for Spotify OAuth confirmation
        """
        params = {
            'client_id': settings.SPOTIFY['client_id'],
            'response_type': 'code',
            'scope': ' '.join(settings.SPOTIFY['auth_user_scopes']),
            'redirect_uri': settings.SPOTIFY['auth_redirect_uri'],
            'state': state
        }

        return '{url}?{params}'.format(url=settings.SPOTIFY['user_auth_url'], params=urlencode(params))

    def get_access_and_refresh_tokens(self, code):
        """
        Make a request to the Spotify authorization endpoint to obtain the access and refresh tokens for a user after
        they have granted our application permission to Spotify on their behalf.

        :param code: (str) Authorization code returned from initial request to SPOTIFY['user_auth_url']

        :return: (dict)
            - access_token (str)
            - refresh_token (str)
        """
        data = {
            'grant_type': 'authorization_code',  # Constant; From Spotify documentation
            'code': code,
            'redirect_uri': settings.SPOTIFY['auth_redirect_uri'],
        }

        headers = self._make_authorization_header()

        response = self._make_spotify_request('POST', settings.SPOTIFY['auth_url'], data=data, headers=headers)

        return {
            'access_token': response['access_token'],
            'refresh_token': response['refresh_token']
        }

    def refresh_access_token(self, refresh_token):
        """
        Refresh application on behalf of user given a refresh token. On a successful response, will return an
        access token for the user good for the timeout period for Spotify authentication (One hour.)

        :param refresh_token: (str) Refresh token for user (stored in `SpotifyUserAuth`

        :return: (str) New access token for user
        """
        data = {
            'grant_type': 'refresh_token',  # Constant; From Spotify documentation
            'refresh_token': refresh_token
        }

        headers = self._make_authorization_header()

        response = self._make_spotify_request('POST', settings.SPOTIFY['auth_url'], headers=headers, data=data)

        return response['access_token']

    def get_user_profile(self, access_token):
        """
        Get data on the user from Spotify API /me endpoint

        :param access_token: (str) OAuth token from Spotify for the user

        :return: (dict) Payload for the given user
        """
        url = '{api_url}/me'.format(api_url=settings.SPOTIFY['api_url'])
        headers = {'Authorization': 'Bearer {}'.format(access_token)}

        return self._make_spotify_request('GET', url, headers=headers)

    def get_attributes_for_track(self, uri):
        """
        Fetch song metadata for a singular track

        :param uri: (str) URI of song to search for on Spotify

        :return: (dict)
            - name (str)
            - artist (str)
            - code (str)
        """
        song_id = self.get_code_from_spotify_uri(uri)
        url = '{api_url}/tracks/{id}'.format(
            api_url=settings.SPOTIFY['api_url'],
            id=song_id
        )

        track = self._make_spotify_request('GET', url)

        return {
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'code': uri
        }

    def get_user_playlists(self, auth_code, spotify_user_id):
        """
        Get all playlists for the given Spotify user.

        :param auth_code: (str) SpotifyUserAuth access_token for the given user
        :param spotify_user_id: (str) Spotify username for the given user

        :return: (dict) Spotify response for all users playlists
        """
        url = '{api_url}/users/{user_id}/playlists'.format(
            api_url=settings.SPOTIFY['api_url'],
            user_id=spotify_user_id
        )

        headers = {
            'Authorization': 'Bearer {}'.format(auth_code),
            'Content-Type': 'application/json'
        }

        return self._make_spotify_request('GET', url, headers=headers)

    def create_playlist(self, auth_code, spotify_user_id, playlist_name):
        """
        Create a playlist for the given Spotify user. Note that this creates an empty playlist,
        a subsequent API call should be made to populate the playlist with songs.

        :param auth_code: (str) SpotifyUserAuth access_token for the given user
        :param spotify_user_id: (str) Spotify username for the given user
        :param playlist_name: (str) Name of the playlist to be created

        :return: (str) Spotify playlist ID for the created playlist
        """
        url = '{api_url}/users/{user_id}/playlists'.format(
            api_url=settings.SPOTIFY['api_url'],
            user_id=spotify_user_id
        )

        headers = {
            'Authorization': 'Bearer {}'.format(auth_code),
            'Content-Type': 'application/json'
        }

        data = {
            'name': playlist_name,
            'public': True
        }

        resp = self._make_spotify_request('POST', url, headers=headers, data=json.dumps(data))

        return resp['id']

    def add_songs_to_playlist(self, auth_code, playlist_id, songs):
        """
        Add songs to a specified playlist

        :param auth_code: (str) SpotifyUserAuth access_token for the given user
        :param playlist_id: (str) Spotify playlist ID to add songs to
        :param songs: (list) Collection of Spotify track URIs to add to playlist
        """
        url = '{api_url}/playlists/{playlist_id}/tracks'.format(
            api_url=settings.SPOTIFY['api_url'],
            playlist_id=playlist_id
        )

        headers = {
            'Authorization': 'Bearer {}'.format(auth_code),
            'Content-Type': 'application/json'
        }

        data = {'uris': songs}

        self._make_spotify_request('POST', url, headers=headers, data=json.dumps(data))

    def delete_songs_from_playlist(self, auth_code, playlist_id, songs):
        """
        Remove songs from a specified playlist

        :param auth_code: (str) SpotifyUserAuth access_token for the given user
        :param playlist_id: (str) Spotify playlist ID to remove songs from
        :param songs: (list) Collection of Spotify track URIs to remove from playlist
        """
        url = '{api_url}/playlists/{playlist_id}/tracks'.format(
            api_url=settings.SPOTIFY['api_url'],
            playlist_id=playlist_id
        )

        headers = {
            'Authorization': 'Bearer {}'.format(auth_code),
            'Content-Type': 'application/json'
        }

        data = {'uris': songs}

        self._make_spotify_request('DELETE', url, headers=headers, data=json.dumps(data))

    def get_user_top_artists(self, auth_code):
        """
        Retrieve the top artists from Spotify for a user.

        :param auth_code: (str) SpotifyUserAuth access_token for the given user

        :return: (list(str)) List of top artists for the user from Spotify
        """
        url = '{api_url}/me/top/artists'.format(api_url=settings.SPOTIFY['api_url'])

        headers = {'Authorization': 'Bearer {}'.format(auth_code)}
        params = {'limit': settings.SPOTIFY['max_top_artists']}

        resp = self._make_spotify_request('GET', url, headers=headers, params=params)

        # Parse the response for the artist name values
        artists = []
        for item in resp['items']:
            artists.append(item['name'])

        return artists
