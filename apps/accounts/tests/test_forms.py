from django.test import TestCase

from accounts.forms import UpdateUserInfoForm


class TestUpdateUserInfoForm(TestCase):

    def test_clean_password_values_match(self):
        data = {
            'password': '12345',
            'confirm_password': '12345'
        }

        form = UpdateUserInfoForm(data)
        self.assertTrue(form.is_valid())

    def test_clean_password_values_do_not_match(self):
        data = {
            'password': '12345',
            'confirm_password': '67890'
        }

        form = UpdateUserInfoForm(data)
        self.assertFalse(form.is_valid())
