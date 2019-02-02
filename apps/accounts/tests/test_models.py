from unittest import mock

from django.conf import settings
from django.db.utils import IntegrityError
from django.db.models.signals import post_save
from django.test import TestCase

from accounts.models import MoodyUser, UserEmotion, UserSongVote
from accounts.signals import create_user_emotion_records
from tunes.models import Emotion
from libs.tests.helpers import SignalDisconnect, MoodyUtil


class TestUserEmot(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Disable signal that creates UserEmotion records on user creation
        # so we can create ones during testing
        dispatch_uid = 'user_post_save_create_useremotion_records'
        with SignalDisconnect(post_save, create_user_emotion_records,
                              settings.AUTH_USER_MODEL, dispatch_uid):
            cls.user = MoodyUtil.create_user(username='test_user')

    def test_uniqueness_on_user_emot_fields(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        UserEmotion.objects.create(user=self.user, emotion=emotion)

        with self.assertRaises(IntegrityError):
            UserEmotion.objects.create(user=self.user, emotion=emotion)

    def test_update_emotion_boundaries(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        user_emot = UserEmotion.objects.create(user=self.user, emotion=emotion)

        valence = .5
        energy = .5

        expected_new_energy = (emotion.energy + energy) / 2
        expected_new_valence = (emotion.valence + valence) / 2

        user_emot.update_emotion_boundaries(valence, energy)
        self.assertEqual(user_emot.energy, expected_new_energy)
        self.assertEqual(user_emot.valence, expected_new_valence)

    def test_reset_emotion_boundaries(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        user_emot = UserEmotion.objects.create(user=self.user, emotion=emotion)

        valence = .5
        energy = .5

        expected_new_energy = 2 * emotion.energy - energy
        expected_new_valence = 2 * emotion.valence - valence

        user_emot.update_emotion_boundaries(valence, energy, reset=True)
        self.assertEqual(user_emot.energy, expected_new_energy)
        self.assertEqual(user_emot.valence, expected_new_valence)


class TestMoodyUser(TestCase):
    @mock.patch('django.contrib.auth.base_user.AbstractBaseUser.set_password')
    def test_update_information(self, mock_password_update):
        user = MoodyUser.objects.create(username='test_user')
        data = {
            'username': 'new_name',
            'email': 'foo@example.com',
            'password': '12345',
            'foo': 'bar'  # Invalid value, just to ensure method doesn't blow up
        }

        user.update_information(data)
        user.refresh_from_db()

        self.assertEqual(user.username, data['username'])
        self.assertEqual(user.email, data['email'])
        mock_password_update.assert_called_with(data['password'])


class TestUserSongVote(TestCase):
    @classmethod
    def setUpTestData(cls):
        util = MoodyUtil()
        cls.user = util.create_user()
        cls.song = util.create_song()
        cls.emotion = Emotion.objects.get(name=Emotion.HAPPY)

    def test_deleting_vote_resets_boundaries(self):
        user_emot = self.user.useremotion_set.get(emotion__name=Emotion.HAPPY)

        expected_new_energy = user_emot.energy
        expected_new_valence = user_emot.valence

        vote = UserSongVote.objects.create(
            user=self.user,
            emotion=self.emotion,
            song=self.song,
            vote=True
        )

        vote.delete()

        user_emot.refresh_from_db()

        self.assertEqual(user_emot.energy, expected_new_energy)
        self.assertEqual(user_emot.valence, expected_new_valence)
