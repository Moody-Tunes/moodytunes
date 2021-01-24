from django.db.models import FloatField
from django.utils.translation import gettext_lazy as _
from rest_framework.fields import ChoiceField

from base.validators import validate_decimal_value


class CleanedChoiceField(ChoiceField):
    """Choice fields that does not print the input value in response on error"""
    default_error_messages = {
        'invalid_choice': _('Not a valid choice for option.')
    }


class UnitIntervalField(FloatField):
    """A FloatField that validates the value supplied is between 0 and 1"""
    default_validators = [validate_decimal_value]
    description = _("Floating point number between 0 ad 1 (inclusive)")
