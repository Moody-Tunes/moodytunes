from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import MoodyUser, UserSongVote
from tunes.models import Emotion
from libs.tests.helpers import MoodyUtil


class TestProfileView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('accounts:profile')

    def test_login_required(self):
        resp = self.client.get(self.url)
        expected_rediect = '{}?next={}'.format(reverse('accounts:login'), self.url)

        self.assertEqual(resp.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(resp, expected_rediect)


class TestUpdateView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('accounts:update')

    def test_login_required(self):
        resp = self.client.get(self.url)
        expected_rediect = '{}?next={}'.format(reverse('accounts:login'), self.url)

        self.assertEqual(resp.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(resp, expected_rediect)

    def test_happy_path(self):
        user = MoodyUtil.create_user()
        self.client.login(username=user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

        update_data = {
            'username': 'my_new_user',
            'email': 'foo@example.com',
        }

        resp = self.client.post(self.url, data=update_data, follow=True)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertEqual(user.username, update_data['username'])
        self.assertEqual(user.email, update_data['email'])

    def test_updating_password_redirect_to_login(self):
        user = MoodyUtil.create_user()
        self.client.login(username=user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

        update_data = {
            'password': 'superSecret123',
            'confirm_password': 'superSecret123'
        }

        resp = self.client.post(self.url, data=update_data, follow=True)

        expected_redirect = '{}?next={}'.format(reverse('accounts:login'), reverse('accounts:profile'))
        self.assertRedirects(resp, expected_redirect)

    def test_updating_user_with_existing_username_is_rejected(self):
        user = MoodyUtil.create_user()
        other_user = MoodyUtil.create_user(username='something-else')
        self.client.login(username=user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

        request_data = {'username': other_user.username}

        resp = self.client.post(self.url, data=request_data)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(MoodyUser.objects.filter(username=user.username).count(), 1)
        self.assertEqual(MoodyUser.objects.filter(username=other_user.username).count(), 1)
        self.assertIn(b'This username is already taken. Please choose a different one', resp.content)


class TestCreateUserView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('accounts:create')

    def test_happy_path(self):
        user_data = {
            'username': 'new_user',
            'password': 'superSecret123',
            'confirm_password': 'superSecret123'
        }

        resp = self.client.post(self.url, data=user_data)

        self.assertEqual(resp.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(resp, reverse('accounts:login'))
        self.assertTrue(MoodyUser.objects.filter(username=user_data['username']).exists())

    def test_creating_user_with_existing_username_is_rejected(self):
        user = MoodyUtil.create_user()
        request_data = {
            'username': user.username,
            'password': 'superSecret123',
            'confirm_password': 'superSecret123'
        }

        resp = self.client.post(self.url, data=request_data)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(MoodyUser.objects.filter(username=user.username).count(), 1)
        self.assertIn(b'This username is already taken. Please choose a different one', resp.content)


class TestAnalyticsView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('accounts:analytics')
        cls.user = MoodyUtil.create_user()
        cls.api_client = APIClient()

    def setUp(self):
        self.api_client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    def test_unauthenticated_request_is_forbidden(self):
        self.api_client.logout()

        params = {'emotion': Emotion.HAPPY}
        resp = self.api_client.get(self.url, data=params)

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unsupported_method_is_rejected(self):
        data = {'emotion': Emotion.HAPPY}
        resp = self.api_client.post(self.url, data=data)

        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_unknown_emotion_returns_bad_request(self):
        data = {'emotion': 'some-fake-emotion'}
        resp = self.api_client.get(self.url, data=data)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_happy_path(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        upvoted_song_1 = MoodyUtil.create_song(valence=.75, energy=.65)
        upvoted_song_2 = MoodyUtil.create_song(valence=.65, energy=.7)
        downvoted_song = MoodyUtil.create_song(valence=.5, energy=.45)

        UserSongVote.objects.create(user=self.user, emotion=emotion, song=upvoted_song_1, vote=True)
        UserSongVote.objects.create(user=self.user, emotion=emotion, song=upvoted_song_2, vote=True)
        UserSongVote.objects.create(user=self.user, emotion=emotion, song=downvoted_song, vote=False)

        working_songs = [upvoted_song_1, upvoted_song_2]
        user_emotion = self.user.get_user_emotion_record(emotion.name)
        expected_response = {
            'emotion': emotion.name,
            'emotion_name': emotion.full_name,
            'genre': None,
            'energy': user_emotion.energy,
            'valence': user_emotion.valence,
            'total_songs': len(working_songs)
        }

        params = {'emotion': Emotion.HAPPY}
        resp = self.api_client.get(self.url, data=params)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertDictEqual(resp_data, expected_response)

    def test_genre_filter_only_returns_songs_for_genre(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        expected_song = MoodyUtil.create_song(genre='hiphop')
        other_song = MoodyUtil.create_song(genre='something-else')

        UserSongVote.objects.create(
            user=self.user,
            emotion=emotion,
            song=expected_song,
            vote=True
        )

        UserSongVote.objects.create(
            user=self.user,
            emotion=emotion,
            song=other_song,
            vote=True
        )

        user_emotion = self.user.get_user_emotion_record(emotion.name)
        expected_response = {
            'emotion': emotion.name,
            'emotion_name': emotion.full_name,
            'genre': expected_song.genre,
            'energy': user_emotion.energy,
            'valence': user_emotion.valence,
            'total_songs': 1,
        }

        params = {'emotion': Emotion.HAPPY, 'genre': expected_song.genre}
        resp = self.api_client.get(self.url, data=params)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertDictEqual(resp_data, expected_response)

    def test_user_with_no_votes_returns_defaults(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)

        user_emotion = self.user.get_user_emotion_record(emotion.name)
        expected_response = {
            'emotion': emotion.name,
            'emotion_name': emotion.full_name,
            'genre': None,
            'energy': user_emotion.energy,
            'valence': user_emotion.valence,
            'total_songs': 0
        }

        params = {'emotion': Emotion.HAPPY}
        resp = self.api_client.get(self.url, data=params)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertDictEqual(resp_data, expected_response)
