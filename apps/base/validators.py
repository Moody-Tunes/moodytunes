from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_decimal_value(value):
    """Validate `value` is between 0 <= value <= 1"""
    if value < 0 or value > 1:
        raise ValidationError(
            _('{} must be between 0 and 1'.format(value)),
            params={'value': value}
        )
