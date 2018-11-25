from base64 import b64encode
import logging
import random

from django.conf import settings
from django.core.cache import cache

import requests
from requests.exceptions import HTTPError

logger = logging.getLogger(__name__)


class SpotifyException(Exception):
    """Exception to raise in case something bad happens during request"""
    pass


class SpotifyClient(object):
    """Wrapper around the Spotify API"""
    def __init__(self, command_id=None):
        self._unique_id = command_id
        self.seen_songs = []

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
        logger.info('{id} - Making {method} request to Spotify URL: {url}. GET data: {GET} . POST data: {POST}'.format(
            id=self._unique_id,
            method=method,
            url=url,
            GET=params,
            POST=data
        ))

        if not headers:
            # Retrieve the header we need to make an auth request
            auth_token = self._get_auth_access_token()
            headers = {'Authorization': 'Bearer {}'.format(auth_token)}

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

            logger.info('{} - Successful request made to {}. Response: {}'.format(self._unique_id, url, response))

        except HTTPError:
            logger.warning('{} - Received HTTPError requesting {}'.format(self._unique_id, url), exc_info=True)
            response = {}

        except Exception:
            logger.error('{} - Received unhandled exception requesting {}'.format(self._unique_id, url), exc_info=True)
            response = {}

        return response

    def _get_auth_access_token(self):
        """
        Return the access token we need to make requests to Spotify. Will either hit the cache for the key,
        or make a request to Spotify if the token in the cache is invalid
        @return access_token: (str) Key needed to authenticate with Spotify API
        """
        access_token = cache.get(settings.SPOTIFY['auth_cache_key'])

        if not access_token:
            logger.info('{} - Cache miss for auth access token'.format(self._unique_id))
            access_token = self._make_auth_access_token_request()

            if access_token:
                cache.set(settings.SPOTIFY['auth_cache_key'], access_token, settings.SPOTIFY['auth_cache_key_timeout'])
            else:
                logger.warning('{} - Unable to retrieve access token from Spotify'.format(self._unique_id))

                raise SpotifyException('Unable to retrieve Spotify access token')

        return access_token

    def _make_auth_access_token_request(self):
        """
        Get an access token from Spotify for authentication
        @return access_token: Token used for authentication with Spotify (str)
        """
        auth_val = '{client_id}:{secret_key}'.format(
            client_id=settings.SPOTIFY['client_id'],
            secret_key=settings.SPOTIFY['secret_key']
        )
        auth_val = bytes(auth_val, encoding='utf-8')
        auth_header = b64encode(auth_val)

        headers = {
            'Authorization': 'Basic {}'.format(auth_header.decode('utf8'))
        }

        data = {'grant_type': 'client_credentials'}

        resp = self._make_spotify_request(
            'POST',
            settings.SPOTIFY['auth_url'],
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
            api_url=settings.SPOTIFY['api_url'],
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
            - code (str): Spotify ID of the song
        """
        url = '{api_url}/users/{user_id}/playlists/{playlist_id}'.format(
            api_url=settings.SPOTIFY['api_url'],
            user_id=playlist['user'],
            playlist_id=playlist['uri']
        )

        params = {'fields': 'tracks(items(track(id,uri,name,artists,explicit)))'}

        response = self._make_spotify_request('GET', url, params=params)

        if not response:
            logger.warning('{} - Failed to get songs from playlist {}'.format(self._unique_id, playlist['uri']))

            raise SpotifyException('Unable to fetch songs from playlist {}'.format(playlist['name']))

        processed_tracks = 0
        retrieved_tracks = []

        tracks = response['tracks']['items']
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
                'name': track['track']['name'].encode('utf-8'),
                'artist': track['track']['artists'][0]['name'].encode('utf-8'),
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
        Get audio features for a number of tracks. Currently returns sentiment and valence data for the track from
        Spotify. Will update the track in place, each track in the list is a dictionary of values needed to create a
        Song object. This track returns the list with the dictionaries updated with the `valence` and `energy` values.

        :param tracks: List of dictionaries representing tracks in Spotify
        @return tracks: Same list before updated with audio feature data included
        """
        batch_size = 100

        # Create a list of lists of tracks, each one being at most batch_size length
        # Spotify allows up to 100 songs to be processed at once
        batched_tracks = [tracks[idx:idx + batch_size] for idx in range(0, len(tracks), batch_size)]

        for batch in batched_tracks:
            # Construct query params list from track ids in batch
            url = '{api_url}/audio-features'.format(
                api_url=settings.SPOTIFY['api_url']
            )

            # Strip spotify:track: from the uri (Spotify just wants the id)
            track_ids = [track['code'].split(':')[2] for track in batch]
            params = {'ids': ','.join([track_id for track_id in track_ids])}

            response = self._make_spotify_request(
                'GET',
                url,
                params=params
            )

            # Response is returned in the order requested (req:[1,2,3] -> res:[1,2,3])
            # If an object is not found, a null value is returned in the appropriate position
            for track, track_data in zip(batch, response['audio_features']):
                # If a song is not found, Spotify returns `None`
                if track_data:
                    valence = track_data.get('valence')
                    energy = track_data.get('energy')

                    # Skip tracks that don't have both attributes we're looking for
                    if not all([valence, energy]):
                        continue

                    track.update({
                        'valence': valence,
                        'energy': energy
                    })

        return tracks
