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
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()

    def test_valid_emotion_is_valid(self):
        data = {'emotion': Emotion.HAPPY}
        form = PlaylistForm(data, user=self.user)

        self.assertTrue(form.is_valid())

    def test_invalid_emotion_is_invalid(self):
        data = {'emotion': 'it-be-like-that-sometimes'}
        form = PlaylistForm(data, user=self.user)

        self.assertFalse(form.is_valid())

    def test_valid_context_is_valid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'context': 'WORK'
        }

        form = PlaylistForm(data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_invalid_context_is_invalid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'context': 'PLAY'
        }

        form = PlaylistForm(data, user=self.user)
        self.assertFalse(form.is_valid())

    def test_genre_for_voted_song_is_valid(self):
        song = MoodyUtil.create_song()
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        MoodyUtil.create_user_song_vote(self.user, song, emotion, True)

        data = {
            'emotion': Emotion.HAPPY,
            'genre': song.genre
        }

        form = PlaylistForm(data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_genre_not_in_votes_is_not_valid(self):
        song = MoodyUtil.create_song()
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        MoodyUtil.create_user_song_vote(self.user, song, emotion, True)

        data = {
            'emotion': Emotion.HAPPY,
            'genre': 'some-other-genre'
        }

        form = PlaylistForm(data, user=self.user)
        self.assertFalse(form.is_valid())
