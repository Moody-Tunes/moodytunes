from django.test import TestCase

from accounts.forms import UpdateUserInfoForm, AnalyticsForm
from tunes.models import Emotion
from libs.tests.helpers import MoodyUtil


class TestUpdateUserInfoForm(TestCase):

    def test_clean_password_values_match(self):
        data = {
            'password': '12345',
            'confirm_password': '12345'
        }

        form = UpdateUserInfoForm(data)
        self.assertTrue(form.is_valid())

    def test_clean_password_values_do_not_match(self):
        data = {
            'password': '12345',
            'confirm_password': '67890'
        }

        form = UpdateUserInfoForm(data)
        self.assertFalse(form.is_valid())


class TestAnalyticsForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.song = MoodyUtil.create_song()

    def test_no_genre_is_valid(self):
        data = {'emotion': Emotion.HAPPY}
        form = AnalyticsForm(data)

        self.assertTrue(form.is_valid())

    def test_valid_genre_is_valid(self):
        data = {'genre': self.song.genre, 'emotion': Emotion.HAPPY}
        form = AnalyticsForm(data)

        self.assertTrue(form.is_valid())

    def test_invalid_emotion_is_not_valid(self):
        data = {'emotion': 'some-fake-emotion'}
        form = AnalyticsForm(data)

        self.assertFalse(form.is_valid())

    def test_invalid_genre_is_not_valid(self):
        data = {'genre': 'fake-genre', 'emotion': Emotion.HAPPY}
        form = AnalyticsForm(data)

        self.assertFalse(form.is_valid())
