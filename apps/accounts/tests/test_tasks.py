from django.conf import settings
from django.db.models.signals import post_save
from django.test import TestCase

from accounts.models import MoodyUser, UserSongVote
from accounts.signals import create_user_emotion_records, update_user_emotion_attributes
from accounts.tasks import CreateUserEmotionRecordsForUserTask, UpdateUserEmotionRecordAttributeTask
from tunes.models import Emotion
from libs.tests.helpers import MoodyUtil, SignalDisconnect
from utils import average


class TestCreateUserEmotionTask(TestCase):
    @classmethod
    def setUpTestData(cls):
        dispatch_uid = 'user_post_save_create_useremotion_records'
        with SignalDisconnect(post_save, create_user_emotion_records, settings.AUTH_USER_MODEL, dispatch_uid):
            cls.user = MoodyUtil.create_user(username='test_user')

    def test_happy_path(self):
        CreateUserEmotionRecordsForUserTask().run(self.user.pk)

        self.user.refresh_from_db()

        useremotion_emotion_names = list(self.user.useremotion_set.values_list(
                'emotion__name',
                flat=True
            ).order_by('emotion__name')
        )
        emotion_names = list(Emotion.objects.values_list('name', flat=True).order_by('name'))

        self.assertListEqual(useremotion_emotion_names, emotion_names)

    def test_raises_exception_if_user_not_found(self):
        invalid_user_pk = 10000

        with self.assertRaises(MoodyUser.DoesNotExist):
            CreateUserEmotionRecordsForUserTask().run(invalid_user_pk)


class TestUpdateUserEmotionTask(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.emotion = Emotion.objects.get(name=Emotion.HAPPY)
        cls.song1 = MoodyUtil.create_song(valence=.75, energy=.55)
        cls.song2 = MoodyUtil.create_song(valence=.55, energy=.75)

    def test_happy_path(self):
        dispatch_uid = 'user_song_vote_post_save_update_useremotion_attributes'
        with SignalDisconnect(post_save, update_user_emotion_attributes, UserSongVote, dispatch_uid):
            vote1 = MoodyUtil.create_user_song_vote(self.user, self.song1, self.emotion, True)
            vote2 = MoodyUtil.create_user_song_vote(self.user, self.song2, self.emotion, True)

        UpdateUserEmotionRecordAttributeTask().run(vote1.pk)
        UpdateUserEmotionRecordAttributeTask().run(vote2.pk)

        user_emotion = self.user.get_user_emotion_record(self.emotion.name)
        user_votes = self.user.usersongvote_set.all()

        expected_valence = average(user_votes, 'song__valence')
        expected_energy = average(user_votes, 'song__energy')

        self.assertEqual(user_emotion.valence, expected_valence)
        self.assertEqual(user_emotion.energy, expected_energy)

    def test_raises_exception_if_user_not_found(self):
        invalid_vote_pk = 10000

        with self.assertRaises(UserSongVote.DoesNotExist):
            UpdateUserEmotionRecordAttributeTask().run(invalid_vote_pk)
