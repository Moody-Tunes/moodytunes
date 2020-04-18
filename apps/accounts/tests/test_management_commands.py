import logging
from smtplib import SMTPException
from unittest import mock

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.management import call_command, CommandError
from django.test import TestCase
from django.urls import reverse

from accounts.management.commands.accounts_recover_user_account import Command as RecoverCommand
from tunes.models import Emotion
from libs.tests.helpers import MoodyUtil


@mock.patch('django.core.management.base.OutputWrapper', mock.MagicMock)
class TestRecoverUserAccount(TestCase):

    @mock.patch('accounts.models.MoodyUser.objects.make_random_password')
    def test_happy_patch(self, mock_generate_password):
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


class TestUpdateUserEmotionDanceability(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.emotion = Emotion.objects.get(name=Emotion.EXCITED)

    def test_command_set_empty_value_to_emotion_default(self):
        user_emotion = self.user.get_user_emotion_record(Emotion.EXCITED)
        user_emotion.danceability = 0
        user_emotion.save()

        call_command('accounts_update_user_emotion_danceability')

        user_emotion.refresh_from_db()
        self.assertEqual(user_emotion.danceability, self.emotion.danceability)

    def test_command_does_not_override_previous_danceability_value(self):
        song1 = MoodyUtil.create_song(danceability=.75)
        song2 = MoodyUtil.create_song(danceability=.95)
        MoodyUtil.create_user_song_vote(self.user, song1, self.emotion, True)
        MoodyUtil.create_user_song_vote(self.user, song2, self.emotion, True)

        user_emotion = self.user.get_user_emotion_record(Emotion.EXCITED)
        old_user_emotion_danceability = user_emotion.danceability

        call_command('accounts_update_user_emotion_danceability')

        user_emotion.refresh_from_db()
        self.assertEqual(user_emotion.danceability, old_user_emotion_danceability)
