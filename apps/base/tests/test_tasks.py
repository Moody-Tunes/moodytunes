from datetime import timedelta

from django.conf import settings
from django.contrib.sessions.models import Session
from django.test import TestCase
from django.utils import timezone

from base.tasks import ClearExpiredSessionsTask


class TestClearExpiredSessionsTask(TestCase):
    def test_happy_path(self):
        expired_session_date = timezone.now() - timedelta(seconds=settings.SESSION_COOKIE_AGE + 1)
        Session.objects.create(
            session_data='foobar',
            session_key='bizbaz',
            expire_date=expired_session_date
        )

        ClearExpiredSessionsTask().run()
        self.assertEqual(Session.objects.count(), 0)
