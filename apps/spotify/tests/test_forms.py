from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from libs.tests.helpers import MoodyUtil
from spotify.forms import ExportPlaylistForm, SuggestSongForm
from tunes.models import Emotion


class TestSuggestSongForm(TestCase):
    def test_valid_data(self):
        data = {'code': 'spotify:track:6JVU5TollB4mTzMkb5d8Z9'}
        form = SuggestSongForm(data)

        self.assertTrue(form.is_valid())

    def test_suggestion_for_existing_song_is_invalid(self):
        song = MoodyUtil.create_song()

        data = {'code': song.code}
        form = SuggestSongForm(data)

        self.assertFalse(form.is_valid())

    def test_invalid_song_code_is_invalid(self):
        data = {'code': 'some-fake-code'}
        form = SuggestSongForm(data)

        self.assertFalse(form.is_valid())


class TestExportPlaylistForm(TestCase):
    def test_valid_data(self):
        data = {
            'emotion': Emotion.HAPPY,
            'playlist_name': 'test_playlist'
        }

        form = ExportPlaylistForm(data)
        self.assertTrue(form.is_valid())

    def test_valid_genre_is_valid(self):
        song = MoodyUtil.create_song()

        data = {
            'emotion': Emotion.HAPPY,
            'playlist_name': 'test_playlist',
            'genre': song.genre
        }

        form = ExportPlaylistForm(data)
        self.assertTrue(form.is_valid())

    def test_valid_context_is_valid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'playlist_name': 'test_playlist',
            'context': 'WORK'
        }

        form = ExportPlaylistForm(data)
        self.assertTrue(form.is_valid())

    def test_invalid_emotion_is_invalid(self):
        data = {
            'emotion': 'fake-emotion',
            'playlist_name': 'test_playlist'
        }

        form = ExportPlaylistForm(data)
        self.assertFalse(form.is_valid())

    def test_invalid_playlist_name_is_invalid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'playlist_name': 'a' * 110  # Max playlist name length is 100 characters
        }

        form = ExportPlaylistForm(data)
        self.assertFalse(form.is_valid())

    def test_invalid_genre_is_invalid(self):
        MoodyUtil.create_song()

        data = {
            'emotion': Emotion.HAPPY,
            'playlist_name': 'test_playlist',
            'genre': 'fake-genre'
        }

        form = ExportPlaylistForm(data)
        self.assertFalse(form.is_valid())

    def test_invalid_context_is_invalid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'playlist_name': 'test_playlist',
            'context': 'invalid-context'
        }

        form = ExportPlaylistForm(data)
        self.assertFalse(form.is_valid())

    def test_valid_image_upload_is_valid(self):
        with open('{}/apps/spotify/tests/fixtures/cat.jpg'.format(settings.BASE_DIR), 'rb') as img_file:
            img = SimpleUploadedFile('my_cover.jpg', img_file.read())

        data = {
            'emotion': Emotion.HAPPY,
            'playlist_name': 'test_playlist',
        }

        files = {'cover_image': img}

        form = ExportPlaylistForm(data, files)
        self.assertTrue(form.is_valid())

    def test_invalid_image_upload_is_invalid(self):
        with open('{}/apps/spotify/tests/fixtures/hack.php'.format(settings.BASE_DIR), 'rb') as hack_file:
            hack = SimpleUploadedFile('hack.php', hack_file.read())

        data = {
            'emotion': Emotion.HAPPY,
            'playlist_name': 'test_playlist',
        }

        files = {'cover_image': hack}

        form = ExportPlaylistForm(data, files)
        self.assertFalse(form.is_valid())
