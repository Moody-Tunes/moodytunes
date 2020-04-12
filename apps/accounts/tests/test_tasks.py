from django.conf import settings
from django.db.models.signals import post_save
from django.test import TestCase

from accounts.models import MoodyUser
from accounts.signals import create_user_emotion_records
from accounts.tasks import create_user_emotion_records_for_user
from tunes.models import Emotion
from libs.tests.helpers import MoodyUtil, SignalDisconnect


class TestCreateUserEmotionTask(TestCase):
    @classmethod
    def setUpTestData(cls):
        dispatch_uid = 'user_post_save_create_useremotion_records'
        with SignalDisconnect(post_save, create_user_emotion_records, settings.AUTH_USER_MODEL, dispatch_uid):
            cls.user = MoodyUtil.create_user(username='test_user')

    def test_happy_path(self):
        create_user_emotion_records_for_user.run(self.user.pk)

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
            create_user_emotion_records_for_user.run(invalid_user_pk)
