from unittest import mock

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import MoodyUser, UserSongVote
from tunes.models import Emotion
from libs.tests.helpers import MoodyUtil, get_messages_from_response
from libs.utils import average


class TestLoginView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('accounts:login')
        cls.user = MoodyUtil.create_user()

    def test_login_redirects_to_valid_path(self):
        next = reverse('moodytunes:browse')
        url = self.url + '?next={}'.format(next)

        data = {
            'username': self.user.username,
            'password': MoodyUtil.DEFAULT_USER_PASSWORD
        }

        resp = self.client.post(url, data=data)

        self.assertRedirects(resp, next)

    def test_login_redirect_to_default(self):
        data = {
            'username': self.user.username,
            'password': MoodyUtil.DEFAULT_USER_PASSWORD
        }

        resp = self.client.post(self.url, data=data)

        self.assertRedirects(resp, settings.LOGIN_REDIRECT_URL)

    def test_login_returns_bad_request_for_invalid_path(self):
        next = '6330599317423175408.owasp.org'
        url = self.url + '?next={}'.format(next)

        data = {
            'username': self.user.username,
            'password': MoodyUtil.DEFAULT_USER_PASSWORD
        }

        resp = self.client.post(url, data=data)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class TestProfileView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('accounts:profile')

    def test_login_required(self):
        resp = self.client.get(self.url)
        expected_redirect = '{}?next={}'.format(reverse('accounts:login'), self.url)

        self.assertEqual(resp.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(resp, expected_redirect)


class TestUpdateView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('accounts:update')

    def test_login_required(self):
        resp = self.client.get(self.url)
        expected_redirect = '{}?next={}'.format(reverse('accounts:login'), self.url)

        self.assertEqual(resp.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(resp, expected_redirect)

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
        user_votes = self.user.get_user_song_vote_records(emotion.name)
        expected_response = {
            'emotion': emotion.name,
            'emotion_name': emotion.full_name,
            'genre': None,
            'energy': average([vote.song.energy for vote in user_votes if vote.vote]),
            'valence': average([vote.song.valence for vote in user_votes if vote.vote]),
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
        other_song = MoodyUtil.create_song(genre='something-else', energy=.3, valence=.25)

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

        # We should only see the average energy and valence
        # for the songs in the genre
        expected_response = {
            'emotion': emotion.name,
            'emotion_name': emotion.full_name,
            'genre': expected_song.genre,
            'energy': expected_song.energy,
            'valence': expected_song.valence,
            'total_songs': 1,
        }

        params = {'emotion': Emotion.HAPPY, 'genre': expected_song.genre}
        resp = self.api_client.get(self.url, data=params)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertDictEqual(resp_data, expected_response)

    def test_user_with_no_votes_returns_no_analytics(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)

        expected_response = {
            'emotion': emotion.name,
            'emotion_name': emotion.full_name,
            'genre': None,
            'energy': None,
            'valence': None,
            'total_songs': 0
        }

        params = {'emotion': Emotion.HAPPY}
        resp = self.api_client.get(self.url, data=params)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertDictEqual(resp_data, expected_response)

    def test_multiple_votes_for_same_song_only_returns_one_count(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        expected_song = MoodyUtil.create_song()

        # Make one vote without a context and one with a context
        UserSongVote.objects.create(
            user=self.user,
            emotion=emotion,
            song=expected_song,
            vote=True,
        )

        UserSongVote.objects.create(
            user=self.user,
            emotion=emotion,
            song=expected_song,
            vote=True,
            context='WORK'
        )

        # We should only see the song once in the response
        user_emotion = self.user.get_user_emotion_record(emotion.name)
        expected_response = {
            'emotion': emotion.name,
            'emotion_name': emotion.full_name,
            'genre': None,
            'energy': user_emotion.energy,
            'valence': user_emotion.valence,
            'total_songs': 1,
        }

        params = {'emotion': Emotion.HAPPY}
        resp = self.api_client.get(self.url, data=params)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertDictEqual(resp_data, expected_response)

    def test_endpoint_return_analytics_for_context_if_provided(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        expected_song = MoodyUtil.create_song()
        other_song = MoodyUtil.create_song(energy=.75, valence=.65)

        UserSongVote.objects.create(
            user=self.user,
            emotion=emotion,
            song=expected_song,
            vote=True,
            context='WORK'
        )

        UserSongVote.objects.create(
            user=self.user,
            emotion=emotion,
            song=other_song,
            vote=True,
            context='PARTY'
        )

        # We should only see the song for this context in the response
        expected_response = {
            'emotion': emotion.name,
            'emotion_name': emotion.full_name,
            'genre': None,
            'energy': expected_song.energy,
            'valence': expected_song.valence,
            'total_songs': 1,
        }

        params = {
            'emotion': Emotion.HAPPY,
            'context': 'WORK'
        }
        resp = self.api_client.get(self.url, data=params)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertDictEqual(resp_data, expected_response)

    def test_endpoint_handles_context_and_genre_filters(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        expected_song = MoodyUtil.create_song(genre='first-genre')
        other_song = MoodyUtil.create_song(genre='second-genre', energy=.75, valence=.65)

        # Create matrix of expected song and context
        UserSongVote.objects.create(
            user=self.user,
            emotion=emotion,
            song=expected_song,
            vote=True,
            context='WORK'
        )

        UserSongVote.objects.create(
            user=self.user,
            emotion=emotion,
            song=other_song,
            vote=True,
            context='WORK'
        )

        UserSongVote.objects.create(
            user=self.user,
            emotion=emotion,
            song=expected_song,
            vote=True,
            context='PARTY'
        )

        UserSongVote.objects.create(
            user=self.user,
            emotion=emotion,
            song=other_song,
            vote=True,
            context='PARTY'
        )

        # We should only see the expected song for this context and genre in the response
        expected_response = {
            'emotion': emotion.name,
            'emotion_name': emotion.full_name,
            'genre': expected_song.genre,
            'energy': expected_song.energy,
            'valence': expected_song.valence,
            'total_songs': 1,
        }

        params = {
            'emotion': Emotion.HAPPY,
            'genre': expected_song.genre,
            'context': 'WORK'
        }
        resp = self.api_client.get(self.url, data=params)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertDictEqual(resp_data, expected_response)


class TestMoodyPasswordResetView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('accounts:reset-password')
        cls.user = MoodyUtil.create_user(email='foo@example.com')

    @mock.patch('django.contrib.auth.tokens.PasswordResetTokenGenerator.make_token')
    @mock.patch('django.contrib.auth.forms.PasswordResetForm.send_mail')
    def test_happy_path(self, mock_send_mail, mock_token_generator):
        mock_token_generator.return_value = 'foo-bar'
        expected_redirect = reverse('accounts:login')
        data = {'email': self.user.email}

        resp = self.client.post(self.url, data=data)

        self.assertRedirects(resp, expected_redirect)

        messages = get_messages_from_response(resp)
        self.assertIn('We have sent a password reset email to the address provided', messages)

        email_context = {
            'email': 'foo@example.com',
            'domain': 'testserver',
            'site_name': 'testserver',
            'uid': 'MQ',
            'user': self.user,
            'token': mock_token_generator(),
            'protocol': 'http'
        }

        mock_send_mail.assert_called_once_with(
            'registration/password_reset_subject.txt',
            'password_reset_email.html',
            email_context,
            None,  # From email, defaults to DEFAULT_FROM_EMAIL
            self.user.email,
            html_email_template_name=None
        )

    @mock.patch('django.contrib.auth.forms.PasswordResetForm.send_mail')
    def test_bad_email_is_rejected(self, mock_send_mail):
        data = {'email': 'bad-data'}

        resp = self.client.post(self.url, data=data)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('Enter a valid email address.', resp.context['form'].errors['email'])

        mock_send_mail.assert_not_called()


class TestMoodyPasswordResetConfirmView(TestCase):
    def test_happy_path(self):
        user = MoodyUtil.create_user(email='foo@example.com')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = PasswordResetTokenGenerator().make_token(user)

        url = reverse('accounts:password-reset-confirm', kwargs={'uidb64': uid, 'token': token})

        initial_resp = self.client.get(url)
        reset_url = initial_resp['Location']

        expected_redirect = reverse('accounts:password-reset-complete')
        data = {
            'new_password1': 'password',
            'new_password2': 'password'
        }

        resp = self.client.post(reset_url, data=data)

        self.assertRedirects(resp, expected_redirect, fetch_redirect_response=False)

        # Test password updated OK
        user.refresh_from_db()
        updated_user = authenticate(username=user.username, password=data['new_password1'])

        self.assertEqual(user.pk, updated_user.pk)

    def test_non_matching_passwords_are_rejected(self):
        user = MoodyUtil.create_user(email='foo@example.com')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = PasswordResetTokenGenerator().make_token(user)

        url = reverse('accounts:password-reset-confirm', kwargs={'uidb64': uid, 'token': token})

        initial_resp = self.client.get(url)
        reset_url = initial_resp['Location']

        data = {
            'new_password1': 'foo',
            'new_password2': 'bar'
        }

        resp = self.client.post(reset_url, data=data)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("The two password fields didn't match.", resp.context['form'].errors['new_password2'])


class TestMoodyPasswordResetDone(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('accounts:password-reset-complete')

    def test_happy_path(self):
        expected_redirect = reverse('accounts:login')
        resp = self.client.get(self.url)

        self.assertRedirects(resp, expected_redirect)

        messages = get_messages_from_response(resp)
        self.assertIn('Please login with your new password', messages)
