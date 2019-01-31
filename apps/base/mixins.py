import copy
import logging

from base.responses import BadRequest

logger = logging.getLogger(__name__)


class MoodyMixin(object):
    """Base class for mixins in mtdj"""


class ValidateRequestDataMixin(MoodyMixin):
    """
    Mixin to verify incoming request data. This class contains logic to validate incoming request data for various
    REST methods.

    To use the functionality for this class, inherit from it and define the relevant form to use in verifying data for
    the specific method. For example, if your view has GET functionality and you want to validate the incoming data,
    you should override the `get_request_serializer` attribute on the class.
    """

    # Dictionary mapping request method to instance attribute containing data for the request
    REQUEST_DATA_MAPPING = {
        'GET': 'query_params',
        'POST': 'data',
        'DELETE': 'data'
    }

    def __init__(self):
        self.cleaned_data = {}  # Cleaned data for request
        self.data = None   # Used in cases where we're reading the request body (POST, DELETE)
        super().__init__()

    def _clean_headers(self, headers):
        """
        Remove sensitive header information from headers before logging
        :param headers: (dict) Request headers to be stripped.
        :return: (dict) Headers with sensitive information from it
        """
        sensitive_headers = ['HTTP_AUTHORIZATION']
        stripped_value = '********'

        def __strip_cookie(cookie_string):
            sensitive_cookies = ['sessionid']

            cookies = cookie_string.split(';')
            cookie_dict = dict([cookie.split('=') for cookie in cookies])

            for name, value in cookie_dict.items():
                if name in sensitive_cookies:
                    cookie_dict[name] = stripped_value

            return cookie_dict

        for name, value in headers.items():
            if name == 'HTTP_COOKIE':
                headers[name] = __strip_cookie(copy.deepcopy(value).strip())

            if name in sensitive_headers:
                headers[name] = stripped_value

        return headers

    def _log_bad_request(self, request):
        """Log information about a request if something fails to validate"""
        request_data = {
            'params': request.GET,
            'data': request.data if request.data else request.body,
            'user_id': request.user.id,
            'headers': self._clean_headers(copy.deepcopy(request.META)),
            'method': request.method,
        }

        logger.warning(
            'Invalid {} data supplied to {}'.format(request.method, self.__class__.__name__),
            extra=request_data
        )

    def _validate_request(self, request):
        serializer_class = getattr(self, '{}_request_serializer'.format(request.method.lower()), None)

        if serializer_class:
            data = getattr(request, self.REQUEST_DATA_MAPPING[request.method], {})
            self.data = data
            serializer = serializer_class(data=data)

            if serializer.is_valid():
                self.cleaned_data = serializer.data
                return True
            else:
                self._log_bad_request(request)
                return False
        else:
            raise AttributeError(
                '{} received a {} request but did not defined a form class for this method. '
                'Please set the {} attribute on this view to process this request'.format(
                    self.__class__,
                    request.method,
                    '{}_request_serializer'.format(request.method.lower())
                )
            )


class GetRequestValidatorMixin(ValidateRequestDataMixin):
    get_request_serializer = None

    def get(self, request, *args, **kwargs):
        if self._validate_request(request):
            return super(GetRequestValidatorMixin, self).get(request, *args, **kwargs)
        else:
            return BadRequest()


class PostRequestValidatorMixin(ValidateRequestDataMixin):
    post_request_serializer = None

    def post(self, request, *args, **kwargs):
        if self._validate_request(request):
            return super(PostRequestValidatorMixin, self).post(request, *args, **kwargs)
        else:
            return BadRequest()


class DeleteRequestValidatorMixin(ValidateRequestDataMixin):
    delete_request_serializer = None

    def delete(self, request, *args, **kwargs):
        if self._validate_request(request):
            return super(DeleteRequestValidatorMixin, self).delete(request, *args, **kwargs)
        else:
            return BadRequest()
