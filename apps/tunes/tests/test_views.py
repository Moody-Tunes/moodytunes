from django.test import TestCase
from django.urls import reverse

from rest_framework import status

from accounts.models import UserSongVote
from tunes.models import Emotion
from libs.tests.helpers import MoodyUtil


class TestBrowseView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('tunes:browse')
        cls.user = MoodyUtil.create_user()

    def setUp(self):
        self.client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    def test_unauthenticated_request_is_forbidden(self):
        self.client.logout()
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unknown_emotion_passed_returns_bad_request(self):
        params = {
            'emotion': 'unknown'
        }

        resp = self.client.get(self.url, data=params)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_happy_path(self):
        song = MoodyUtil.create_song(energy=.75, valence=.75)
        params = {
            'emotion': Emotion.HAPPY,
            'jitter': 0
        }

        resp = self.client.get(self.url, data=params)
        resp_song = resp.json()[0]

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_song['id'], song.id)


class TestVoteView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('tunes:vote')
        cls.user = MoodyUtil.create_user()
        cls.song = MoodyUtil.create_song()

    def setUp(self):
        self.client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    def test_unauthenticated_request_is_forbidden(self):
        self.client.logout()

        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code,
            'vote': True
        }
        resp = self.client.post(self.url, data=data)

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_happy_path(self):
        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code,
            'vote': True
        }
        resp = self.client.post(self.url, data=data)

        vote_created = UserSongVote.objects.filter(
            user=self.user,
            emotion__name=Emotion.HAPPY,
            song=self.song,
            vote=True
        ).exists()

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(vote_created)

    def test_bad_request_if_invalid_data_sent(self):
        # Missing vote value
        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code,
        }
        resp = self.client.post(self.url, data=data)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bad_request_if_bad_emotion_sent(self):
        data = {
            'emotion': 'Bad emotion',
            'song_code': self.song.code,
            'vote': True
        }
        resp = self.client.post(self.url, data=data)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bad_request_if_bad_song_code_sent(self):





        data = {
            'emotion': Emotion.HAPPY,
            'song_code': 'Bad song code',
            'vote': True
        }
        resp = self.client.post(self.url, data=data)

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_upvoting_on_song_updates_user_emotion_boundaries(self):
        user_emotion = self.user.useremotion_set.get(emotion__name=Emotion.HAPPY)
        pre_upper_bound = user_emotion.upper_bound
        pre_lower_bound = user_emotion.lower_bound

        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code,
            'vote': True
        }
        self.client.post(self.url, data=data)

        user_emotion.refresh_from_db()
        expected_upper_bound = (pre_upper_bound + self.song.valence) / 2
        expected_lower_bound = (pre_lower_bound + self.song.energy) / 2

        self.assertEqual(user_emotion.upper_bound, expected_upper_bound)
        self.assertEqual(user_emotion.lower_bound, expected_lower_bound)

    def test_downvoting_on_song_does_not_update_user_emotion_boundaries(self):
        user_emotion = self.user.useremotion_set.get(emotion__name=Emotion.HAPPY)
        pre_upper_bound = user_emotion.upper_bound
        pre_lower_bound = user_emotion.lower_bound

        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code,
            'vote': False
        }
        self.client.post(self.url, data=data)

        user_emotion.refresh_from_db()

        self.assertEqual(user_emotion.upper_bound, pre_upper_bound)
        self.assertEqual(user_emotion.lower_bound, pre_lower_bound)
