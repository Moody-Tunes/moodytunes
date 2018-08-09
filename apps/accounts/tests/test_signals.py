from django.test import TestCase

from accounts.models import MoodyUser
from tunes.models import Emotion


class TestCreateUserEmotionRecordsSignal(TestCase):

    def test_post_save_user_creates_all_user_emotion_records(self):
        user = MoodyUser.objects.create(username='test_signal_user')

        existing_emotions = Emotion.objects.all().order_by('-name')
        created_user_emotions = user.useremotion_set.all().order_by(
            '-emotion__name'
            ).values_list(
            'emotion__name',
            flat=True
        )

        self.assertQuerysetEqual(existing_emotions, created_user_emotions)
