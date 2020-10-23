from unittest import mock

from django.test import TestCase

from accounts.utils import log_failed_login_attempt


class TestLogFailedLoginAttempt(TestCase):
    @mock.patch('accounts.utils.logger')
    def test_log_failed_login_attempt(self, mock_logger):
        username = 'test'
        ip_address = '1.2.3.4'

        credentials = {'username': username}
        request = mock.Mock()
        request.META = {'HTTP_X_FORWARDED_FOR': ip_address}

        log_failed_login_attempt(credentials, request)

        mock_logger.warning.assert_called_once_with(
            'Failed login attempt for {}'.format(username),
            extra={
                'fingerprint': 'accounts.utils.log_failed_login_attempt',
                'username': username,
                'ip_address': ip_address,
            }
        )
