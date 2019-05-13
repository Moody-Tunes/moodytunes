from django.utils.translation import ugettext_lazy as _
from rest_framework.fields import ChoiceField


class CleanedChoiceField(ChoiceField):
    """Choice fields that does not echo the input value in response on error"""
    default_error_messages = {
        'invalid_choice': _('Not a valid choice for option.')
    }
