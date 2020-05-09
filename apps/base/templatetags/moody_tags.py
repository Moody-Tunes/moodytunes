from django import template
from django.conf import settings as django_settings
from django.template.defaultfilters import stringfilter


register = template.Library()


@register.simple_tag
@stringfilter
def settings(value):
    """Return settings.VALUE from Django config module. Returns empty string if not found"""
    return getattr(django_settings, value.upper(), '')
