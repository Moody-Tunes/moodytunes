from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import UserSongVote
from tunes.models import Emotion
from libs.tests.helpers import MoodyUtil


class TestBrowseView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.api_client = APIClient()
        cls.url = reverse('tunes:browse')
        cls.user = MoodyUtil.create_user()

    def setUp(self):
        self.api_client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    def test_unauthenticated_request_is_forbidden(self):
        self.api_client.logout()

        params = {'emotion': Emotion.HAPPY}
        resp = self.api_client.get(self.url, data=params)

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_query_params_passed_returns_bad_request(self):
        resp = self.api_client.get(self.url)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_emotion_passed_returns_bad_request(self):
        params = {'emotion': 'unknown'}
        resp = self.api_client.get(self.url, data=params)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_happy_path(self):
        song = MoodyUtil.create_song(energy=.75, valence=.75)
        params = {
            'emotion': Emotion.HAPPY,
            'jitter': 0
        }

        resp = self.api_client.get(self.url, data=params)
        resp_song = resp.json()[0]

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_song['id'], song.id)

    def test_filter_on_genre(self):
        MoodyUtil.create_song()
        expected_song = MoodyUtil.create_song(genre='super-dope')
        params = {
            'emotion': Emotion.HAPPY,
            'jitter': 0,
            'genre': expected_song.genre
        }

        resp = self.api_client.get(self.url, data=params)
        resp_song = resp.json()[0]

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_song['id'], expected_song.id)

    def test_playlist_respects_limit(self):
        for _ in range(10):
            MoodyUtil.create_song()

        params = {
            'emotion': Emotion.HAPPY,
            'jitter': 0,
            'limit': 5
        }

        resp = self.api_client.get(self.url, data=params)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_data), params['limit'])

    def test_playlist_excludes_previously_voted_songs(self):
        voted_song = MoodyUtil.create_song()
        not_voted_song = MoodyUtil.create_song()

        UserSongVote.objects.create(
            user=self.user,
            song=voted_song,
            emotion=Emotion.objects.get(name=Emotion.HAPPY),
            vote=True
        )

        params = {
            'emotion': Emotion.HAPPY,
            'jitter': 0
        }

        resp = self.api_client.get(self.url, data=params)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_data), 1)
        self.assertEqual(resp_data[0]['id'], not_voted_song.id)


class TestVoteView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.api_client = APIClient()
        cls.url = reverse('tunes:vote')
        cls.user = MoodyUtil.create_user()
        cls.song = MoodyUtil.create_song()

    def setUp(self):
        self.api_client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    def test_unauthenticated_request_is_forbidden(self):
        self.api_client.logout()

        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code,
            'vote': True
        }
        resp = self.api_client.post(self.url, data=data, format='json')

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_post_data_passed_returns_bad_request(self):
        resp = self.api_client.post(self.url)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_delete_data_passed_returns_bad_request(self):
        resp = self.api_client.delete(self.url)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_happy_path(self):
        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code,
            'vote': True
        }
        resp = self.api_client.post(self.url, data=data, format='json')

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
        resp = self.api_client.post(self.url, data=data, format='json')

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bad_request_if_bad_emotion_sent(self):
        data = {
            'emotion': 'Bad emotion',
            'song_code': self.song.code,
            'vote': True
        }
        resp = self.api_client.post(self.url, data=data, format='json')

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bad_request_if_bad_song_code_sent(self):
        data = {
            'emotion': Emotion.HAPPY,
            'song_code': 'Bad song code',
            'vote': True
        }
        resp = self.api_client.post(self.url, data=data, format='json')

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
        self.api_client.post(self.url, data=data, format='json')

        user_emotion.refresh_from_db()
        expected_upper_bound = (pre_upper_bound + self.song.valence) / 2
        expected_lower_bound = (pre_lower_bound + self.song.energy) / 2

        self.assertEqual(user_emotion.upper_bound, expected_upper_bound)
        self.assertEqual(user_emotion.lower_bound, expected_lower_bound)

    def test_downvoting_song_does_not_update_user_emotion_boundaries(self):
        user_emotion = self.user.useremotion_set.get(emotion__name=Emotion.HAPPY)
        pre_upper_bound = user_emotion.upper_bound
        pre_lower_bound = user_emotion.lower_bound

        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code,
            'vote': False
        }
        self.api_client.post(self.url, data=data, format='json')

        user_emotion.refresh_from_db()

        self.assertEqual(user_emotion.upper_bound, pre_upper_bound)
        self.assertEqual(user_emotion.lower_bound, pre_lower_bound)

    def test_delete_happy_path(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)

        vote_record = UserSongVote.objects.create(
            user=self.user,
            emotion=emotion,
            song=self.song,
            vote=True
        )

        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code
        }

        resp = self.api_client.delete(self.url, data=data, format='json')
        vote_record.refresh_from_db()

        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(vote_record.vote)

    def test_delete_bad_request_data(self):
        data = {
            'emotion': 'foobarbaz',
            'song_code': self.song.code
        }

        resp = self.api_client.delete(self.url, data=data, format='json')

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_vote_not_found(self):
        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code
        }

        resp = self.api_client.delete(self.url, data=data, format='json')

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_vote_conflict(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)

        UserSongVote.objects.create(
            user=self.user,
            emotion=emotion,
            song=self.song,
            vote=True
        )
        UserSongVote.objects.create(
            user=self.user,
            emotion=emotion,
            song=self.song,
            vote=True
        )

        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code
        }

        resp = self.api_client.delete(self.url, data=data, format='json')

        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)


class TestPlaylistView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.api_client = APIClient()
        cls.url = reverse('tunes:playlist')
        cls.user = MoodyUtil.create_user()
        cls.song = MoodyUtil.create_song()

    def setUp(self):
        self.api_client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    def test_unauthenticated_request_is_forbidden(self):
        self.api_client.logout()

        data = {'emotion': Emotion.HAPPY}
        resp = self.api_client.get(self.url, data=data)

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_query_params_passed_returns_bad_request(self):
        resp = self.api_client.get(self.url)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_happy_path(self):
        UserSongVote.objects.create(
            user=self.user,
            song=self.song,
            emotion=Emotion.objects.get(name=Emotion.HAPPY),
            vote=True
        )

        data = {'emotion': Emotion.HAPPY}
        resp = self.api_client.get(self.url, data=data)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_data[0]['id'], self.song.id)

    def test_downvoted_songs_are_not_returned(self):
        UserSongVote.objects.create(
            user=self.user,
            song=self.song,
            emotion=Emotion.objects.get(name=Emotion.HAPPY),
            vote=False
        )

        data = {'emotion': Emotion.HAPPY}
        resp = self.api_client.get(self.url, data=data)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_data), 0)

    def test_filter_playlist_by_genre(self):
        new_song = MoodyUtil.create_song(genre='super-dope')
        UserSongVote.objects.create(
            user=self.user,
            song=self.song,
            emotion=Emotion.objects.get(name=Emotion.HAPPY),
            vote=True
        )
        UserSongVote.objects.create(
            user=self.user,
            song=new_song,
            emotion=Emotion.objects.get(name=Emotion.HAPPY),
            vote=True
        )

        data = {
            'emotion': Emotion.HAPPY,
            'genre': new_song.genre
        }
        resp = self.api_client.get(self.url, data=data)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_data), 1)
        self.assertEqual(resp_data[0]['id'], new_song.id)

    def test_invalid_emotion_returns_bad_request(self):
        data = {'emotion': 'some-bad-value'}
        resp = self.api_client.get(self.url, data=data)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class TestOptionsView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('tunes:options')
        cls.user = MoodyUtil.create_user()
        cls.song = MoodyUtil.create_song()
        cls.api_client = APIClient()

    def setUp(self):
        self.api_client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    def test_unauthenticated_request_is_forbidden(self):
        self.api_client.logout()

        resp = self.api_client.get(self.url)

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_happy_path(self):
        expected_emotions = [{'name': emotion.full_name, 'code': emotion.name} for emotion in Emotion.objects.all()]
        expected_genres = [self.song.genre]
        expected_response = {
            'emotions': expected_emotions,
            'genres': expected_genres
        }

        resp = self.api_client.get(self.url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertDictEqual(resp.json(), expected_response)
