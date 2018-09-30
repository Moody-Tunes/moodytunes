from django.test import TestCase

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
