from unittest import mock

from django.test import TestCase

from accounts.models import SpotifyUserAuth
from libs.tests.helpers import MoodyUtil
from tunes.models import Emotion


class TestCreateUserEmotionRecordsSignal(TestCase):

    def test_post_save_user_creates_all_user_emotion_records(self):
        user = MoodyUtil.create_user(username='test_signal_user')

        existing_emotions = Emotion.objects.all()

        for emotion in existing_emotions:
            self.assertTrue(user.useremotion_set.filter(emotion__name=emotion.name).exists())

    def test_post_save_admin_does_not_create_user_emotion_records(self):
        user = MoodyUtil.create_user(username='test_signal_admin', is_superuser=True)
        self.assertFalse(user.useremotion_set.all())


class TestUpdateSpotifyTopArtistsSignal(TestCase):
    @mock.patch('accounts.tasks.UpdateTopArtistsFromSpotifyTask.apply_async')
    def test_task_is_only_called_on_create(self, mock_task):
        user = MoodyUtil.create_user()
        data = {
            'user': user,
            'spotify_user_id': 'spotify_user',
            'access_token': 'access_token',
            'refresh_token': 'refresh_token'
        }

        auth = SpotifyUserAuth.objects.create(**data)

        mock_task.assert_called_once_with((auth.pk,), countdown=30)

        auth.save()
        self.assertEqual(mock_task.call_count, 1)
