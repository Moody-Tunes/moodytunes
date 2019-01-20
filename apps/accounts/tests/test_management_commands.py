from unittest import mock

from django.contrib.auth import authenticate
from django.core.management import call_command, CommandError
from django.test import TestCase

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
