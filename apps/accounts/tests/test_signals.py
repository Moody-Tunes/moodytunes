from django.test import TestCase

from accounts.models import UserSongVote
from tunes.models import Emotion
from libs.tests.helpers import MoodyUtil


class TestCreateUserEmotionRecordsSignal(TestCase):

    def test_post_save_user_creates_all_user_emotion_records(self):
        user = MoodyUtil.create_user(username='test_signal_user')

        existing_emotions = Emotion.objects.all().order_by('-name')
        created_user_emotions = user.useremotion_set.all().order_by(
            '-emotion__name'
            ).values_list(
            'emotion__name',
            flat=True
        )

        self.assertQuerysetEqual(existing_emotions, created_user_emotions)


class TestUpdateUserBoundariesSignal(TestCase):
    @classmethod
    def setUpTestData(cls):
        util = MoodyUtil()
        cls.user = util.create_user()
        cls.song = util.create_song()
        cls.emotion = Emotion.objects.get(name=Emotion.HAPPY)

    def test_upvoting_song_updates_boundaries(self):
        user_emot = self.user.useremotion_set.get(emotion__name=Emotion.HAPPY)

        expected_new_upper_bound = (user_emot.upper_bound + self.song.valence) / 2
        expected_new_lower_bound = (user_emot.lower_bound + self.song.energy) / 2

        UserSongVote.objects.create(
            user=self.user,
            emotion=self.emotion,
            song=self.song,
            vote=True
        )

        user_emot.refresh_from_db()

        self.assertEqual(user_emot.upper_bound, expected_new_upper_bound)
        self.assertEqual(user_emot.lower_bound, expected_new_lower_bound)

    def test_downvoting_song_does_not_update_boundaries(self):
        user_emot = self.user.useremotion_set.get(emotion__name=Emotion.HAPPY)

        expected_new_upper_bound = user_emot.upper_bound
        expected_new_lower_bound = user_emot.lower_bound

        UserSongVote.objects.create(
            user=self.user,
            emotion=self.emotion,
            song=self.song,
            vote=False
        )

        user_emot.refresh_from_db()

        self.assertEqual(user_emot.upper_bound, expected_new_upper_bound)
        self.assertEqual(user_emot.lower_bound, expected_new_lower_bound)
