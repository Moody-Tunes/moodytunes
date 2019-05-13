from django.test import TestCase
from rest_framework.exceptions import ValidationError

from base.fields import CleanedChoiceField


class TestCleanedChoiceField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.choice = 'FOO'
        cls.choices = [(cls.choice, 'Test Choice')]
        cls.form = CleanedChoiceField(cls.choices)

    def test_valid_choice_is_valid(self):
        resp = self.form.run_validation(self.choice)
        self.assertEqual(resp, self.choice)

    def test_invalid_choice_is_not_displayed_in_error(self):
        invalid_choice = '%3Cscript%3Ealert%281%29%3B%3C%2Fscript'  # From ZAP scan

        with self.assertRaises(ValidationError) as context:
            self.form.run_validation(invalid_choice)

        self.assertNotIn(invalid_choice, context.exception.args[0])
