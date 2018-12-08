from django.test import TestCase

from tunes.forms import BrowseSongsForm, PlaylistSongsForm
from tunes.models import Emotion
from libs.tests.helpers import MoodyUtil


class TestBrowseSongsForm(TestCase):
    def test_valid_emotion_name_is_valid(self):
        data = {'emotion': Emotion.HAPPY}
        form = BrowseSongsForm(data)

        self.assertTrue(form.is_valid())

    def test_invalid_emotion_name_is_not_valid(self):
        data = {'emotion': 'it be like that sometimes'}
        form = BrowseSongsForm(data)

        self.assertFalse(form.is_valid())


class TestPlaylistSongsForm(TestCase):

    def test_valid_genre_is_valid(self):
        song = MoodyUtil.create_song()
        data = {
            'emotion': Emotion.HAPPY,
            'genre': song.genre
        }
        form = PlaylistSongsForm(data)

        self.assertTrue(form.is_valid())

    def test_invalid_genre_is_invalid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'genre': 'some-fake-genre'
        }
        form = PlaylistSongsForm(data)

        self.assertFalse(form.is_valid())

    def test_valid_emotion_name_is_valid(self):
        data = {'emotion': Emotion.HAPPY}
        form = PlaylistSongsForm(data)

        self.assertTrue(form.is_valid())

    def test_invalid_emotion_name_is_not_valid(self):
        data = {'emotion': 'it be like that sometimes'}
        form = PlaylistSongsForm(data)

        self.assertFalse(form.is_valid())
