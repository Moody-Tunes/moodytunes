import logging


logger = logging.getLogger(__name__)


def log_failed_login_attempt(credentials, request, **kwargs):
    """
    Log a failed login attempt from the given request with the given credentials

    :param credentials: (dict) Username/password combination sent in the login request
    :param request: (django.http.HttpRequest) Request object for the login request
    """
    username = credentials['username']
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
    host = request.host.name

    logger.warning(
        'Failed login attempt for {}'.format(username),
        extra={
            'fingerprint': 'accounts.utils.log_failed_login_attempt',
            'username': username,
            'ip_address': ip_address,
            'host': host
        }
    )
