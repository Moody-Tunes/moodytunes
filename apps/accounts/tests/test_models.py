from django.db.utils import IntegrityError
from django.db.models.signals import post_save
from django.test import TestCase

from accounts.models import MoodyUser, UserEmotion
from accounts.signals import create_user_emotion_records
from tunes.models import Emotion
from libs.tests_helpers import SignalDisconnect


class TestUserEmot(TestCase):
    def test_uniqueness_on_user_emot_fields(self):
        dispatch_uid = 'user_post_save_create_useremotion_records'
        with SignalDisconnect(post_save, create_user_emotion_records,
                              MoodyUser, dispatch_uid):
            user = MoodyUser.objects.create(username='test_user')
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        UserEmotion.objects.create(user=user, emotion=emotion)

        with self.assertRaises(IntegrityError):
            UserEmotion.objects.create(user=user, emotion=emotion)
