from django.test import TestCase

from moodytunes.forms import BrowseForm, PlaylistForm
from tunes.models import Emotion
from libs.tests.helpers import MoodyUtil


class TestBrowseForm(TestCase):
    def test_valid_emotion_is_valid(self):
        data = {'emotion': Emotion.HAPPY}
        form = BrowseForm(data)

        self.assertTrue(form.is_valid())

    def test_invalid_emotion_is_invalid(self):
        data = {'emotion': 'it-be-like-that-sometimes'}
        form = BrowseForm(data)

        self.assertFalse(form.is_valid())

    def test_valid_context_is_valid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'context': 'WORK'
        }

        form = BrowseForm(data)
        self.assertTrue(form.is_valid())

    def test_invalid_context_is_invalid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'context': 'PLAY'
        }

        form = BrowseForm(data)
        self.assertFalse(form.is_valid())

    def test_genre_for_song_in_system_is_valid(self):
        song = MoodyUtil.create_song()
        data = {
            'emotion': Emotion.HAPPY,
            'genre': song.genre
        }

        form = BrowseForm(data)
        self.assertTrue(form.is_valid())

    def test_fake_genre_is_not_valid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'genre': 'something-fake'
        }

        form = BrowseForm(data)
        self.assertFalse(form.is_valid())


class TestPlaylistForm(TestCase):
    def test_valid_emotion_is_valid(self):
        data = {'emotion': Emotion.HAPPY}
        form = BrowseForm(data)

        self.assertTrue(form.is_valid())

    def test_invalid_emotion_is_invalid(self):
        data = {'emotion': 'it-be-like-that-sometimes'}
        form = PlaylistForm(data)

        self.assertFalse(form.is_valid())

    def test_valid_context_is_valid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'context': 'WORK'
        }

        form = PlaylistForm(data)
        self.assertTrue(form.is_valid())

    def test_invalid_context_is_invalid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'context': 'PLAY'
        }

        form = PlaylistForm(data)
        self.assertFalse(form.is_valid())

    def test_genre_for_song_in_system_is_valid(self):
        song = MoodyUtil.create_song()
        data = {
            'emotion': Emotion.HAPPY,
            'genre': song.genre
        }

        form = PlaylistForm(data)
        self.assertTrue(form.is_valid())

    def test_fake_genre_is_not_valid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'genre': 'something-fake'
        }

        form = PlaylistForm(data)
        self.assertFalse(form.is_valid())
