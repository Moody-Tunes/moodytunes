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

    @mock.patch('base.tasks.call_command')
    @mock.patch('base.tasks.logger')
    def test_management_command_raising_exception_logs_exception(self, mock_logger, mock_call_command):
        mock_call_command.side_effect = Exception
        clear_expired_sessions.run()
        mock_logger.exception.assert_called_once_with('Caught exception when trying to clear expired sessions')
