from django.test import TestCase

from tunes.forms import BrowseSongsForm
from tunes.models import Emotion


class TestBrowseSongsForm(TestCase):
    def test_valid_emotion_name_is_valid(self):
        data = {'emotion': Emotion.HAPPY}
        form = BrowseSongsForm(data)

        self.assertTrue(form.is_valid())

    def test_invalid_emotion_name_is_not_valid(self):
        data = {'emotion': 'it be like that sometimes'}
        form = BrowseSongsForm(data)

        self.assertFalse(form.is_valid())
