from django.utils.translation import gettext_lazy as _
from rest_framework.fields import ChoiceField


class CleanedChoiceField(ChoiceField):
    """Choice fields that does not print the input value in response on error"""
    default_error_messages = {
        'invalid_choice': _('Not a valid choice for option.')
    }
