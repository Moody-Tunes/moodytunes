from unittest import mock

from django.test import TestCase

from accounts.utils import log_failed_login_attempt


class TestLogFailedLoginAttempt(TestCase):
    @mock.patch('accounts.utils.logger')
    def test_log_failed_login_attempt(self, mock_logger):
        username = 'test'
        ip_address = '1.2.3.4'
        host = 'www'
        trace_id = 'test-trace-id'

        credentials = {'username': username}
        request = mock.Mock()
        request.META = {'HTTP_X_FORWARDED_FOR': ip_address}
        request.host.name = host
        request.trace_id = trace_id

        log_failed_login_attempt(credentials, request)

        mock_logger.warning.assert_called_once_with(
            'Failed login attempt for {}'.format(username),
            extra={
                'fingerprint': 'accounts.utils.log_failed_login_attempt',
                'username': username,
                'ip_address': ip_address,
                'application_host': host,
                'trace_id': trace_id
            }
        )
