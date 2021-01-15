from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.test import TestCase

from accounts.models import MoodyUser, UserEmotion, UserSongVote
from accounts.signals import create_user_emotion_records, update_user_emotion_attributes
from accounts.tasks import CreateUserEmotionRecordsForUserTask, UpdateUserEmotionRecordAttributeTask
from libs.tests.helpers import MoodyUtil, SignalDisconnect
from libs.utils import average
from tunes.models import Emotion


class TestCreateUserEmotionTask(TestCase):
    @classmethod
    def setUpTestData(cls):
        dispatch_uid = settings.CREATE_USER_EMOTION_RECORDS_SIGNAL_UID
        with SignalDisconnect(post_save, create_user_emotion_records, settings.AUTH_USER_MODEL, dispatch_uid):
            cls.user = MoodyUtil.create_user(username='test_user')

    def test_happy_path(self):
        CreateUserEmotionRecordsForUserTask().run(self.user.pk)

        # Ensure we create one UserEmotion record per Emotion record for the user
        self.assertEqual(self.user.useremotion_set.count(), Emotion.objects.count())

    def test_task_raises_exception_if_user_not_found(self):
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
        dispatch_uid = settings.UPDATE_USER_EMOTION_ATTRIBUTES_SIGNAL_UID
        with SignalDisconnect(post_save, update_user_emotion_attributes, UserSongVote, dispatch_uid):
            MoodyUtil.create_user_song_vote(self.user, self.song1, self.emotion, True)
            MoodyUtil.create_user_song_vote(self.user, self.song2, self.emotion, True)

        UpdateUserEmotionRecordAttributeTask().run(self.user.pk, self.emotion.pk)

        user_emotion = self.user.get_user_emotion_record(self.emotion.name)
        user_votes = self.user.usersongvote_set.all()

        expected_attributes = average(user_votes, 'song__valence', 'song__energy', 'song__danceability')
        expected_valence = expected_attributes['song__valence__avg']
        expected_energy = expected_attributes['song__energy__avg']
        expected_danceability = expected_attributes['song__danceability__avg']

        self.assertEqual(user_emotion.valence, expected_valence)
        self.assertEqual(user_emotion.energy, expected_energy)
        self.assertEqual(user_emotion.danceability, expected_danceability)

    def test_task_creates_user_emotion_record_if_it_does_not_exist(self):
        user_emotion = self.user.get_user_emotion_record(self.emotion.name)
        user_emotion.delete()

        UpdateUserEmotionRecordAttributeTask().run(self.user.pk, self.emotion.pk)

        self.assertTrue(UserEmotion.objects.filter(user=self.user, emotion=self.emotion).exists())

    def test_task_raises_exception_if_user_not_found(self):
        invalid_user_id = 10000

        with self.assertRaises(ValidationError):
            UpdateUserEmotionRecordAttributeTask().run(invalid_user_id, self.emotion.id)

    def test_task_raises_exception_if_emotion_not_found(self):
        invalid_emotion_id = 10000

        with self.assertRaises(Emotion.DoesNotExist):
            UpdateUserEmotionRecordAttributeTask().run(self.user.id, invalid_emotion_id)
