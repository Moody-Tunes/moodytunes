import logging
from smtplib import SMTPException
from unittest import mock

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.urls import reverse

from accounts.management.commands.accounts_recover_user_account import Command as RecoverCommand
from libs.tests.helpers import MoodyUtil


class TestRecoverUserAccountCommand(TestCase):
    @mock.patch('accounts.models.MoodyUser.objects.make_random_password')
    def test_happy_path(self, mock_generate_password):
        user = MoodyUtil.create_user()
        password = '12345'
        mock_generate_password.return_value = password

        call_command('accounts_recover_user_account', user.username)

        user.refresh_from_db()
        updated_user = authenticate(username=user.username, password=password)

        self.assertEqual(user.pk, updated_user.pk)

    def test_user_not_found_raises_command_error(self):
        with self.assertRaises(CommandError):
            call_command('accounts_recover_user_account', 'some-fake-username')

    @mock.patch('accounts.models.MoodyUser.objects.make_random_password')
    @mock.patch('accounts.management.commands.accounts_recover_user_account.send_mail')
    def test_send_email_to_user_happy_path(self, mock_mail, mock_generate_password):
        user = MoodyUtil.create_user()
        user.email = 'foo@example.com'
        user.save()

        password = '12345'
        mock_generate_password.return_value = password

        call_command('accounts_recover_user_account', user.username)

        expected_body = RecoverCommand.email_body.format(
            password=password,
            site='{}{}'.format(settings.SITE_HOSTNAME, reverse('accounts:login'))
        )

        mock_mail.assert_called_once_with(
            RecoverCommand.email_subject,
            expected_body,
            settings.SYSTEM_EMAIL_ADDRESS,
            [user.email]
        )

    @mock.patch('accounts.management.commands.accounts_recover_user_account.Command.write_to_log_and_output')
    @mock.patch('accounts.management.commands.accounts_recover_user_account.send_mail')
    def test_send_email_to_user_raises_exception(self, mock_mail, mock_logger):
        user = MoodyUtil.create_user()
        user.email = 'foo@example.com'
        user.save()

        exc = SMTPException()
        mock_mail.side_effect = exc

        call_command('accounts_recover_user_account', user.username)

        mock_logger.assert_called_with(
            'Unable to send password reset email to user {}'.format(user.username),
            output_stream='stderr',
            log_level=logging.ERROR,
            extra={'exc': exc}
        )
