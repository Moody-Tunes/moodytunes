from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.forms import BaseUserForm, validate_matching_passwords
from libs.tests.helpers import MoodyUtil


class TestValidateMatchingPassword(TestCase):
    def test_matching_password(self):
        resp = validate_matching_passwords('12345', '12345')
        self.assertIsNone(resp)

    def test_non_matching_password_raises_validation_error(self):
        _, resp = validate_matching_passwords('12345', '67890')
        self.assertIsInstance(resp, ValidationError)


class TestUserForm(TestCase):

    def test_clean_password_values_match(self):
        data = {
            'password': '12345',
            'confirm_password': '12345'
        }

        form = BaseUserForm(data)
        self.assertTrue(form.is_valid())

    def test_clean_password_values_do_not_match(self):
        data = {
            'password': '12345',
            'confirm_password': '67890'
        }

        form = BaseUserForm(data)
        self.assertFalse(form.is_valid())

    def test_clean_username_for_existing_user(self):
        user = MoodyUtil.create_user()
        data = {
            'username': user.username,
            'password': '12345',
            'confirm_password': '12345'
        }

        form = BaseUserForm(data)
        self.assertFalse(form.is_valid())
