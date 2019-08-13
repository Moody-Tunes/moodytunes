from unittest import mock

from django.test import TestCase

from moodytunes.tasks import fetch_song_from_spotify
from tunes.models import Song
from libs.spotify import SpotifyException
from libs.tests.helpers import MoodyUtil


class TestFetchSongFromSpotify(TestCase):
    @mock.patch('libs.spotify.SpotifyClient.get_audio_features_for_tracks')
    @mock.patch('libs.spotify.SpotifyClient.get_attributes_for_track')
    def test_happy_path(self, mock_get_attributes, mock_get_features):
        song_code = 'spotify:track:1234567'

        mock_get_attributes.return_value = {
            'code': song_code,
            'name': 'Sickfit',
            'artist': 'Madlib'
        }

        mock_get_features.return_value = [{
            'code': song_code,
            'name': 'Sickfit'.encode('utf-8'),
            'artist': 'Madlib'.encode('utf-8'),
            'valence': .5,
            'energy': .5
        }]

        fetch_song_from_spotify.run(song_code)

        self.assertTrue(Song.objects.filter(code=song_code).exists())

    @mock.patch('moodytunes.tasks.fetch_song_from_spotify.retry')
    @mock.patch('libs.spotify.SpotifyClient.get_attributes_for_track')
    def test_task_is_retried_on_spotify_error(self, mock_get_attributes, mock_retry):
        mock_get_attributes.side_effect = SpotifyException
        song_code = 'spotify:track:1234567'

        fetch_song_from_spotify.run(song_code)

        mock_retry.assert_called_once()

    @mock.patch('libs.spotify.SpotifyClient.get_audio_features_for_tracks')
    @mock.patch('libs.spotify.SpotifyClient.get_attributes_for_track')
    def test_task_does_not_call_spotify_if_song_already_exists(self, mock_get_attributes, mock_get_features):
        song = MoodyUtil.create_song()

        fetch_song_from_spotify.run(song.code)

        mock_get_attributes.assert_not_called()
        mock_get_features.assert_not_called()
