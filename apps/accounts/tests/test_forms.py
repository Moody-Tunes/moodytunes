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

    def test_clean_username_for_taken_username(self):
        user = MoodyUtil.create_user()
        data = {
            'username': user.username,
            'password': '12345',
            'confirm_password': '12345'
        }

        form = BaseUserForm(data)
        self.assertFalse(form.is_valid())


class TestUpdateUserForm(TestCase):
    def test_clean_password_missing_password_is_valid(self):
        user = MoodyUtil.create_user()
        data = {'username': user.username}

        form = UpdateUserForm(data, user=user)
        self.assertTrue(form.is_valid())

    def test_clean_username_missing_value_is_invalid(self):
        data = {'username': ''}

        form = UpdateUserForm(data)
        self.assertFalse(form.is_valid())
