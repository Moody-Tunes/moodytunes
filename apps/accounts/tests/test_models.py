from django.conf import settings
from django.db.utils import IntegrityError
from django.db.models.signals import post_save
from django.test import TestCase

from accounts.models import MoodyUser, UserEmotion
from accounts.signals import create_user_emotion_records
from tunes.models import Emotion
from libs.tests.helpers import SignalDisconnect


class TestUserEmot(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Disable signal that creates UserEmotion records on user creation
        # so we can create ones during testing
        dispatch_uid = 'user_post_save_create_useremotion_records'
        with SignalDisconnect(post_save, create_user_emotion_records,
                              settings.AUTH_USER_MODEL, dispatch_uid):
            cls.user = MoodyUser.objects.create(username='test_user')

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

        expected_new_upper_bound = (emotion.upper_bound + valence) / 2
        expected_new_lower_bound = (emotion.lower_bound + energy) / 2

        user_emot.update_emotion_boundaries(valence, energy)
        self.assertEqual(user_emot.upper_bound, expected_new_upper_bound)
        self.assertEqual(user_emot.lower_bound, expected_new_lower_bound)


class TestMoodyUser(TestCase):
    def test_update_information(self):
        user = MoodyUser.objects.create(username='test_user')
        data = {
            'username': 'new_name',
            'email': 'foo@example.com',
            'foo': 'bar'  # Invalid value, just to ensure method doesn't blow up
        }

        user.update_information(data)
        user.refresh_from_db()

        self.assertEqual(user.username, data['username'])
        self.assertEqual(user.email, data['email'])
