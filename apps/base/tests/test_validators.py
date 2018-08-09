from django.core.exceptions import ValidationError
from django.test import TestCase

from base.validators import validate_decimal_value


class TestDecimalValidator(TestCase):

    def test_valid_value(self):
        try:
            validate_decimal_value(.5)
        except ValidationError:
            self.fail('Raise ValidationError when we did not want to')

    def test_invalid_greater_than_one(self):
        with self.assertRaises(ValidationError):
            validate_decimal_value(2)

    def test_invalid_less_than_zero(self):
        with self.assertRaises(ValidationError):
            validate_decimal_value(-2)
