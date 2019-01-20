from django.test import TestCase

from accounts.serializers import AnalyticsRequestSerializer
from tunes.models import Emotion
from libs.tests.helpers import MoodyUtil


class TestAnalyticsRequestSerializer(TestCase):
    def test_valid_emotion_name_is_valid(self):
        data = {'emotion': Emotion.HAPPY}
        serializer = AnalyticsRequestSerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_invalid_emotion_name_is_not_valid(self):
        data = {'emotion': 'it be like that sometimes'}
        serializer = AnalyticsRequestSerializer(data=data)

        self.assertFalse(serializer.is_valid())

    def test_valid_genre_is_valid(self):
        song = MoodyUtil.create_song()
        data = {
            'emotion': Emotion.HAPPY,
            'genre': song.genre
        }

        serializer = AnalyticsRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_genre_is_not_valid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'genre': 'fake-genre'
        }

        serializer = AnalyticsRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
