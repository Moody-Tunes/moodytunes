from django.test import TestCase
from django.urls import reverse

from rest_framework import status

from accounts.models import MoodyUser
from tunes.models import Emotion, Song


class TestBrowseView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('tunes:browse')
        cls.password = 'admin'

        cls.user = MoodyUser.objects.create(username='moody')
        cls.user.set_password(cls.password)
        cls.user.save()

    def setUp(self):
        self.client.login(username=self.user.username, password=self.password)

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
        song = Song.objects.create(
            name='Happy Song',
            artist='Pop Singer',
            code='abc:123',
            valence=.75,
            energy=.75
        )
        params = {
            'emotion': Emotion.HAPPY,
            'jitter': 0
        }

        resp = self.client.get(self.url, data=params)
        resp_song = resp.json()[0]

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_song['id'], song.id)
