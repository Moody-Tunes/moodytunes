from unittest import mock

from django.test import TestCase

from accounts.models import SpotifyUserAuth, UserSongVote
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


class TestUpdateUserAttributesSignal(TestCase):
    @classmethod
    def setUpTestData(cls):
        util = MoodyUtil()
        cls.user = util.create_user()
        cls.song = util.create_song()
        cls.emotion = Emotion.objects.get(name=Emotion.HAPPY)

    @mock.patch('accounts.models.UserEmotion.update_attributes')
    def test_upvoting_song_calls_updates_attributes(self, mock_update):
        UserSongVote.objects.create(
            user=self.user,
            emotion=self.emotion,
            song=self.song,
            vote=True
        )

        mock_update.assert_called_once()

    @mock.patch('accounts.models.UserEmotion.update_attributes')
    def test_downvoting_song_does_not_call_update_attributes(self, mock_update):
        UserSongVote.objects.create(
            user=self.user,
            emotion=self.emotion,
            song=self.song,
            vote=False
        )

        mock_update.assert_not_called()

    @mock.patch('accounts.models.UserEmotion.update_attributes')
    def test_deleting_vote_calls_update_attributes(self, mock_update):
        vote = UserSongVote.objects.create(
            user=self.user,
            emotion=self.emotion,
            song=self.song,
            vote=True
        )

        mock_update.reset_mock()

        vote.delete()

        mock_update.assert_called_once()


class TestUpdateSpotifyTopArtistsSignal(TestCase):
    @mock.patch('accounts.tasks.UpdateTopArtistsFromSpotifyTask.delay')
    def test_task_is_only_called_on_create(self, mock_task):
        user = MoodyUtil.create_user()
        data = {
            'user': user,
            'spotify_user_id': 'spotify_user',
            'access_token': 'access_token',
            'refresh_token': 'refresh_token'
        }

        auth = SpotifyUserAuth.objects.create(**data)

        mock_task.assert_called_once_with(auth.pk)

        auth.save()
        self.assertEqual(mock_task.call_count, 1)
