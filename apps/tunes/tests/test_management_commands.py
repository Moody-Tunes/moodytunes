from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from libs.spotify import SpotifyException
from tunes.management.commands.tunes_create_songs_from_spotify import Command as SpotifyCommand
from tunes.models import Song


class TestSpotifyCommand(TestCase):
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

        song = Song.objects.filter(code=self.track_data['code'])
        self.assertTrue(song.exists())

    def test_save_songs_to_database_song_already_exists(self):
        Song.objects.create(**self.track_data)

        success, fail = self.command.save_songs_to_database([self.track_data])
        self.assertEqual(success, 0)
        self.assertEqual(fail, 1)

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

    @mock.patch('libs.spotify.SpotifyClient.get_playlists_for_category')
    def test_spotify_exception_raised_with_no_tracks(self, mock_spotify_request):
        # This test ensures that having Spotify raise an Exception does not blow up the command
        mock_spotify_request.side_effect = SpotifyException('Test Spotify Exception')

        call_command('tunes_create_songs_from_spotify')

        self.assertEqual(Song.objects.count(), 0)

    @mock.patch('libs.spotify.SpotifyClient.get_playlists_for_category')
    @mock.patch('libs.spotify.SpotifyClient.get_songs_from_playlist')
    @mock.patch('libs.spotify.SpotifyClient.get_audio_features_for_tracks')
    def test_spotify_exception_raised_with_some_tracks(self, mock_features, _, mock_playlists):
        # If one category returns some tracks and the next one raises an exception, we should
        # still process the songs we got
        mock_playlists.return_value = [{'user': 'two-tone-killer', 'name': 'Beetz.remote'}]

        mock_features.side_effect = [
            [self.track_data],
            SpotifyException('Test Spotify Exception')
        ]

        call_command('tunes_create_songs_from_spotify')

        self.assertEqual(Song.objects.count(), 1)
