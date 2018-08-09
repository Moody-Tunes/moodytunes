from django.conf import settings
from django.db.utils import IntegrityError
from django.db.models.signals import post_save
from django.test import TestCase

from accounts.models import MoodyUser, UserEmotion
from accounts.signals import create_user_emotion_records
from tunes.models import Emotion
from libs.tests_helpers import SignalDisconnect


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
