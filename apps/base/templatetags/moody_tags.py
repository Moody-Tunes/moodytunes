from django import template
from django.conf import settings as django_settings
from django.template.defaultfilters import stringfilter


register = template.Library()


@register.simple_tag
@stringfilter
def settings(value):
    """Return settings.VALUE from Django config module. Returns empty string if not found"""
    return getattr(django_settings, value.upper(), '')


@register.filter()
def user_agent_is_chrome(request):
    """
    Check if the request User-Agent is in the Chrome family. Used for determining whether or not
    to show the help text for playing full songs through Spotify play buttons, as of
    April 24 2020 this behavior is not available on Chrome browsers.

    :param request: (WSGIRequest) Request object for the given request

    :return: (bool)
    """
    return request.user_agent.browser.family in django_settings.CHROME_USER_AGENT_FAMILIES
