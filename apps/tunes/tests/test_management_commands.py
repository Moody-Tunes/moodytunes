import copy
from unittest import mock

from django.core.management import CommandError, call_command
from django.test import TestCase
from spotify_client.exceptions import SpotifyException

from libs.tests.helpers import generate_random_unicode_string
from tunes.management.commands.tunes_create_songs_from_spotify import Command as SpotifyCommand
from tunes.models import Song


class TestCreateSongsFromSpotifyCommand(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.command = SpotifyCommand()

        cls.track_data = {
            'code': 'song-code',
            'name': 'Sapphire',
            'artist': 'Bonobo',
            'energy': .75,
            'valence': .5,
            'genre': 'Chill-Hop'
        }

    def test_save_songs_to_database_happy_path(self):
        success, fail = self.command.save_songs_to_database([self.track_data])
        self.assertEqual(success, 1)
        self.assertEqual(fail, 0)

        self.assertTrue(Song.objects.filter(code=self.track_data['code']).exists())

    def test_save_songs_to_database_with_unicode_characters(self):
        track_data = {
            'code': 'uni-code',
            'name': generate_random_unicode_string(10),
            'artist': generate_random_unicode_string(10),
            'energy': .75,
            'valence': .5,
            'genre': 'Chill-Hop'
        }

        success, fail = self.command.save_songs_to_database([track_data])
        self.assertEqual(success, 1)
        self.assertEqual(fail, 0)

        self.assertTrue(Song.objects.filter(code=track_data['code']).exists())

    def test_save_songs_to_database_song_already_exists(self):
        Song.objects.create(**self.track_data)

        success, fail = self.command.save_songs_to_database([self.track_data])
        self.assertEqual(success, 0)
        self.assertEqual(fail, 1)

    def test_save_songs_to_database_same_song_with_different_song_metadata(self):
        dupe_song = copy.deepcopy(self.track_data)
        dupe_song['artist'] = 'Other Artist'
        dupe_song['name'] = 'Other Name'

        success, fail = self.command.save_songs_to_database([self.track_data, dupe_song])
        songs_for_data = Song.objects.filter(name=self.track_data['name'], artist=self.track_data['artist'])

        self.assertEqual(success, 1)
        self.assertEqual(fail, 1)
        self.assertEqual(songs_for_data.count(), 1)

    def test_save_songs_to_database_invalid_song_data(self):
        # Missing certain fields
        bad_track_data = {
            'code': 'bad-code',
            'name': 'Kiara',
            'artist': 'Bonobo',
        }

        success, fail = self.command.save_songs_to_database([bad_track_data])
        self.assertEqual(success, 0)
        self.assertEqual(fail, 1)

    @mock.patch('spotify_client.SpotifyClient.search')
    def test_script_raises_command_error_if_no_tracks_retrieved_spotify_exception(self, mock_search):
        mock_search.side_effect = SpotifyException('Test Spotify Exception')

        with self.assertRaises(CommandError):
            call_command('tunes_create_songs_from_spotify')

    @mock.patch('spotify_client.SpotifyClient.search')
    def test_script_raises_command_error_if_no_tracks_retrieved_base_exception(self, mock_search):
        mock_search.side_effect = Exception('Test Exception')

        with self.assertRaises(CommandError):
            call_command('tunes_create_songs_from_spotify')

    @mock.patch('spotify_client.SpotifyClient.get_audio_features_for_tracks')
    @mock.patch('spotify_client.SpotifyClient.search')
    def test_spotify_exception_raised_with_some_tracks_creates_songs_from_retrieved_tracks(
            self,
            mock_search,
            mock_get_audio_features
    ):
        mock_search.side_effect = [
            {
                'tracks': {
                    'items': [{
                        'artists': [{'name': 'Drake'}],
                        'name': 'ROCKSTAR (feat. Roddy Ricch)',
                        'uri': 'spotify:track:7ytR5pFWmSjzHJIeQkgog4'
                    }]
                }
            },
            SpotifyException('Test Spotify Exception')
        ]

        mock_get_audio_features.return_value = [{
            'name': 'ROCKSTAR (feat. Roddy Ricch)',
            'code': 'spotify:track:7ytR5pFWmSjzHJIeQkgog4',
            'artist': 'Drake',
            'valence': .50,
            'energy': .50,
            'danceability': .50
        }]

        call_command('tunes_create_songs_from_spotify')

        self.assertEqual(Song.objects.count(), 1)

    @mock.patch('spotify_client.SpotifyClient.get_audio_features_for_tracks')
    @mock.patch('spotify_client.SpotifyClient.search')
    def test_exception_raised_with_some_tracks_creates_songs_from_retrieved_tracks(
            self,
            mock_search,
            mock_get_audio_features
    ):
        mock_search.side_effect = [
            {
                'tracks': {
                    'items': [{
                        'artists': [{'name': 'Drake'}],
                        'name': 'ROCKSTAR (feat. Roddy Ricch)',
                        'uri': 'spotify:track:7ytR5pFWmSjzHJIeQkgog4'
                    }]
                }
            },
            Exception('Test Spotify Exception')
        ]

        mock_get_audio_features.return_value = [{
            'name': 'ROCKSTAR (feat. Roddy Ricch)',
            'code': 'spotify:track:7ytR5pFWmSjzHJIeQkgog4',
            'artist': 'Drake',
            'valence': .50,
            'energy': .50,
            'danceability': .50
        }]

        call_command('tunes_create_songs_from_spotify')

        self.assertEqual(Song.objects.count(), 1)
