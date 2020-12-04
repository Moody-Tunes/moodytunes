from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.forms import BaseUserForm, UpdateUserForm, validate_matching_passwords
from libs.tests.helpers import MoodyUtil


class TestValidateMatchingPassword(TestCase):
    def test_matching_password(self):
        resp = validate_matching_passwords('12345', '12345')
        self.assertIsNone(resp)

    def test_non_matching_password_raises_validation_error(self):
        _, resp = validate_matching_passwords('12345', '67890')
        self.assertIsInstance(resp, ValidationError)


class TestBaseUserForm(TestCase):
    def test_clean_username_missing_value_is_invalid(self):
        data = {
            'username': '',
            'password': '12345',
            'confirm_password': '12345'
        }

        form = BaseUserForm(data)
        self.assertFalse(form.is_valid())

    def test_clean_password_values_match_is_valid(self):
        data = {
            'username': 'foo',
            'password': '12345',
            'confirm_password': '12345'
        }

        form = BaseUserForm(data)
        self.assertTrue(form.is_valid())

    def test_clean_password_values_do_not_match_is_invalid(self):
        data = {
            'username': 'foo',
            'password': '12345',
            'confirm_password': '67890'
        }

        form = BaseUserForm(data)
        self.assertFalse(form.is_valid())

    def test_clean_password_missing_confirm_password_is_invalid(self):
        data = {
            'username': 'foo',
            'password': '12345',
        }

        form = BaseUserForm(data)
        self.assertFalse(form.is_valid())

    def test_clean_username_for_taken_username_is_invalid(self):
        user = MoodyUtil.create_user()
        data = {
            'username': user.username,
            'password': '12345',
            'confirm_password': '12345'
        }

        form = BaseUserForm(data)
        self.assertFalse(form.is_valid())

    def test_clean_username_for_invalid_username_is_invalid(self):
        data = {
            'username': 'zap" AND "1"="1" --',
            'password': '12345',
            'confirm_password': '12345'
        }

        form = BaseUserForm(data)
        self.assertFalse(form.is_valid())

    def test_clean_email_valid_value_is_valid(self):
        data = {
            'username': 'foo',
            'password': '12345',
            'confirm_password': '12345',
            'email': 'foo@example.com'
        }

        form = BaseUserForm(data)
        self.assertTrue(form.is_valid())

    def test_clean_email_invalid_value_is_invalid(self):
        data = {
            'username': 'foo',
            'password': '12345',
            'confirm_password': '12345',
            'email': 'this-isnt-a-valid-email-address'
        }

        form = BaseUserForm(data)
        self.assertFalse(form.is_valid())


class TestUpdateUserForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()

    def test_clean_username_with_same_username_is_valid(self):
        data = {'username': self.user.username}

        form = UpdateUserForm(data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_clean_username_with_new_valid_username_is_valid(self):
        data = {'username': 'testing_update_username'}

        form = UpdateUserForm(data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_clean_username_missing_value_is_invalid(self):
        data = {'username': ''}

        form = UpdateUserForm(data, user=self.user)
        self.assertFalse(form.is_valid())

    def test_clean_username_for_invalid_username_is_invalid(self):
        data = {'username': 'zap" AND "1"="1" --'}

        form = UpdateUserForm(data, user=self.user)
        self.assertFalse(form.is_valid())

    def test_clean_email_for_valid_email_is_valid(self):
        data = {
            'username': self.user.username,
            'email': 'foo@example.com'
        }

        form = UpdateUserForm(data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_clean_email_for_invalid_email_is_invalid(self):
        data = {
            'username': self.user.username,
            'email': 'this-isnt-an-email-address'
        }

        form = UpdateUserForm(data, user=self.user)
        self.assertFalse(form.is_valid())
