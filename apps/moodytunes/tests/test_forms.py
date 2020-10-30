from unittest import mock

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from libs.tests.helpers import MoodyUtil
from moodytunes.forms import (
    BrowseForm,
    ExportPlaylistForm,
    PlaylistForm,
    SuggestSongForm,
    default_option,
    get_genre_choices,
)
from tunes.models import Emotion


class TestGetGenreChoices(TestCase):
    def test_method_returns_all_song_genres(self):
        hiphop_song = MoodyUtil.create_song(genre='hiphop')
        rock_song = MoodyUtil.create_song(genre='rock')

        expected_choices = [
            default_option[0],
            (hiphop_song.genre, hiphop_song.genre.capitalize()),
            (rock_song.genre, rock_song.genre.capitalize())
        ]

        choices = get_genre_choices()

        self.assertEqual(choices, expected_choices)

    def test_method_omits_empty_genre(self):
        song_with_genre = MoodyUtil.create_song(genre='hiphop')
        MoodyUtil.create_song(genre='')

        expected_choices = [
            default_option[0],
            (song_with_genre.genre, song_with_genre.genre.capitalize()),
        ]

        choices = get_genre_choices()

        self.assertEqual(choices, expected_choices)

    @mock.patch('tunes.models.Song.objects.all')
    @mock.patch('django.core.cache.cache.get')
    def test_method_uses_cached_return_value_if_present(self, mock_cache, mock_song_lookup):
        genres = ['foo']
        mock_cache.return_value = genres

        expected_genres = [('', '-----------'), ('foo', 'Foo')]
        returned_genres = get_genre_choices()

        self.assertEqual(returned_genres, expected_genres)
        mock_song_lookup.assert_not_called()


class TestBrowseForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.form = BrowseForm

    def test_valid_emotion_is_valid(self):
        data = {'emotion': Emotion.HAPPY}
        form = self.form(data)

        self.assertTrue(form.is_valid())

    def test_invalid_emotion_is_invalid(self):
        data = {'emotion': 'it-be-like-that-sometimes'}
        form = self.form(data)

        self.assertFalse(form.is_valid())

    def test_valid_context_is_valid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'context': 'WORK'
        }

        form = self.form(data)
        self.assertTrue(form.is_valid())

    def test_invalid_context_is_invalid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'context': 'PLAY'
        }

        form = self.form(data)
        self.assertFalse(form.is_valid())

    def test_genre_for_song_in_system_is_valid(self):
        song = MoodyUtil.create_song()
        data = {
            'emotion': Emotion.HAPPY,
            'genre': song.genre
        }

        form = self.form(data)
        self.assertTrue(form.is_valid())

    def test_fake_genre_is_not_valid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'genre': 'something-fake'
        }

        form = self.form(data)
        self.assertFalse(form.is_valid())

    def test_valid_artist_is_valid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'artist': 'Beach Fossils'
        }

        form = self.form(data)
        self.assertTrue(form.is_valid())

    def test_artist_input_with_too_long_length_is_invalid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'artist': 'this input is way too long' * 50
        }

        form = self.form(data)
        self.assertFalse(form.is_valid())


class TestPlaylistForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.form = PlaylistForm

    def test_valid_emotion_is_valid(self):
        data = {'emotion': Emotion.HAPPY}
        form = self.form(data)

        self.assertTrue(form.is_valid())

    def test_invalid_emotion_is_invalid(self):
        data = {'emotion': 'it-be-like-that-sometimes'}
        form = self.form(data)

        self.assertFalse(form.is_valid())

    def test_valid_context_is_valid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'context': 'WORK'
        }

        form = self.form(data)
        self.assertTrue(form.is_valid())

    def test_invalid_context_is_invalid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'context': 'PLAY'
        }

        form = self.form(data)
        self.assertFalse(form.is_valid())

    def test_genre_for_song_in_system_is_valid(self):
        song = MoodyUtil.create_song()
        data = {
            'emotion': Emotion.HAPPY,
            'genre': song.genre
        }

        form = self.form(data)
        self.assertTrue(form.is_valid())

    def test_fake_genre_is_not_valid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'genre': 'something-fake'
        }

        form = self.form(data)
        self.assertFalse(form.is_valid())

    def test_valid_artist_is_valid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'artist': 'Beach Fossils'
        }

        form = self.form(data)
        self.assertTrue(form.is_valid())

    def test_artist_input_with_too_long_length_is_invalid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'artist': 'this input is way too long' * 50
        }

        form = self.form(data)
        self.assertFalse(form.is_valid())


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
        with open('{}/apps/moodytunes/tests/fixtures/cat.jpg'.format(settings.BASE_DIR), 'rb') as img_file:
            img = SimpleUploadedFile('my_cover.jpg', img_file.read())

        data = {
            'emotion': Emotion.HAPPY,
            'playlist_name': 'test_playlist',
        }

        files = {'cover_image': img}

        form = ExportPlaylistForm(data, files)
        self.assertTrue(form.is_valid())

    def test_invalid_image_upload_is_invalid(self):
        with open('{}/apps/moodytunes/tests/fixtures/hack.php'.format(settings.BASE_DIR), 'rb') as hack_file:
            hack = SimpleUploadedFile('hack.php', hack_file.read())

        data = {
            'emotion': Emotion.HAPPY,
            'playlist_name': 'test_playlist',
        }

        files = {'cover_image': hack}

        form = ExportPlaylistForm(data, files)
        self.assertFalse(form.is_valid())
