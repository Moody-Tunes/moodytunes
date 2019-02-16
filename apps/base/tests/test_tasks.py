from datetime import datetime, timedelta
from unittest import mock

from django.conf import settings
from django.contrib.sessions.models import Session
from django.test import TestCase

from base.tasks import clear_expired_sessions


class TestClearExpiredSessionsTask(TestCase):
    def test_happy_path(self):
        expired_session_date = datetime.today() - timedelta(seconds=settings.SESSION_COOKIE_AGE + 1)
        Session.objects.create(
            session_data='foobar',
            session_key='bizbaz',
            expire_date=expired_session_date
        )

        clear_expired_sessions.run()
        self.assertEqual(Session.objects.count(), 0)
