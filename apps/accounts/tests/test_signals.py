from unittest import mock

from django.test import TestCase

from accounts.models import UserSongVote
from tunes.models import Emotion
from libs.tests.helpers import MoodyUtil


class TestCreateUserEmotionRecordsSignal(TestCase):

    def test_post_save_user_creates_all_user_emotion_records(self):
        user = MoodyUtil.create_user(username='test_signal_user')

        existing_emotions = Emotion.objects.all()

        for emotion in existing_emotions:
            self.assertTrue(user.useremotion_set.filter(emotion__name=emotion.name).exists())


class TestUpdateUserBoundariesSignal(TestCase):
    @classmethod
    def setUpTestData(cls):
        util = MoodyUtil()
        cls.user = util.create_user()
        cls.song = util.create_song()
        cls.emotion = Emotion.objects.get(name=Emotion.HAPPY)

    @mock.patch('accounts.models.UserEmotion.update_emotion_boundaries')
    def test_upvoting_song_updates_boundaries(self, mock_update):
        vote = UserSongVote.objects.create(
            user=self.user,
            emotion=self.emotion,
            song=self.song,
            vote=True
        )

        mock_update.assert_called_once_with(self.song.valence, self.song.energy)

        # If we save the vote again, we shouldn't trigger another update
        vote.save()
        self.assertEqual(mock_update.call_count, 1)

    @mock.patch('accounts.models.UserEmotion.update_emotion_boundaries')
    def test_downvoting_song_does_not_update_boundaries(self, mock_update):
        UserSongVote.objects.create(
            user=self.user,
            emotion=self.emotion,
            song=self.song,
            vote=False
        )

        mock_update.assert_not_called()
