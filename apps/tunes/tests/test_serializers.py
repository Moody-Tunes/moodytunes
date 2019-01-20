from django.test import TestCase

from tunes.models import Emotion
from tunes.serializers import (
    BrowseSongsRequestSerializer,
    DeleteVoteRequestSerializer,
    PlaylistSongsRequestSerializer,
    VoteSongsRequestSerializer
)
from libs.tests.helpers import MoodyUtil


class TestBrowseSongsRequestSerializer(TestCase):
    def test_valid_emotion_name_is_valid(self):
        data = {'emotion': Emotion.HAPPY}
        serializer = BrowseSongsRequestSerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_invalid_emotion_name_is_not_valid(self):
        data = {'emotion': 'it be like that sometimes'}
        serializer = BrowseSongsRequestSerializer(data=data)

        self.assertFalse(serializer.is_valid())

    def test_valid_jitter_is_valid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'jitter': .5
        }

        serializer = BrowseSongsRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_jitter_is_not_valid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'jitter': 5
        }

        serializer = BrowseSongsRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_valid_limit_is_valid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'limit': 10
        }

        serializer = BrowseSongsRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_limit_is_not_valid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'limit': 100
        }

        serializer = BrowseSongsRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class TestPlaylistSongsRequestSerializer(TestCase):
    def test_valid_emotion_name_is_valid(self):
        data = {'emotion': Emotion.HAPPY}
        serializer = PlaylistSongsRequestSerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_invalid_emotion_name_is_not_valid(self):
        data = {'emotion': 'it be like that sometimes'}
        serializer = PlaylistSongsRequestSerializer(data=data)

        self.assertFalse(serializer.is_valid())


class TestDeleteVoteRequestSerializer(TestCase):
    def test_valid_emotion_name_is_valid(self):
        song = MoodyUtil.create_song()
        data = {
            'emotion': Emotion.HAPPY,
            'song_code': song.code
        }
        serializer = DeleteVoteRequestSerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_invalid_emotion_name_is_not_valid(self):
        song = MoodyUtil.create_song()
        data = {
            'emotion': 'it be like that sometimes',
            'song_code': song.code
        }
        serializer = DeleteVoteRequestSerializer(data=data)

        self.assertFalse(serializer.is_valid())


class TestVoteSongsRequestSerializer(TestCase):
    def test_valid_emotion_name_is_valid(self):
        song = MoodyUtil.create_song()
        data = {
            'emotion': Emotion.HAPPY,
            'song_code': song.code,
            'vote': True
        }
        serializer = VoteSongsRequestSerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_invalid_emotion_name_is_not_valid(self):
        song = MoodyUtil.create_song()
        data = {
            'emotion': 'it be like that sometimes',
            'song_code': song.code,
            'vote': True
        }
        serializer = VoteSongsRequestSerializer(data=data)

        self.assertFalse(serializer.is_valid())
