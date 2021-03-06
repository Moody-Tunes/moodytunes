import copy
import logging

from base.responses import BadRequest
from libs.moody_logging import auto_fingerprint, update_logging_data


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
        'DELETE': 'data',
        'PATCH': 'data',
    }

    def __init__(self):
        self.cleaned_data = {}  # Cleaned data for request
        self.data = None   # Used in cases where we're reading the request body (POST, DELETE)
        self.errors = None  # Errors from the request
        super().__init__()

    def _clean_headers(self, headers):
        """
        Helper method to remove sensitive header information from log messages before
        writing header data to logs.

        :param headers: (dict) Request headers to be stripped.

        :return: (dict)
        """
        sensitive_headers = ['HTTP_AUTHORIZATION', 'HTTP_COOKIE', 'HTTP_X_CSRFTOKEN']
        stripped_value = '********'

        for name in headers:
            if name in sensitive_headers:
                headers[name] = stripped_value

        return headers

    @update_logging_data
    def _log_bad_request(self, request, serializer, **kwargs):
        """
        Helper method to log information about a bad request to our system.

        :param request: (rest_framework.request.Request) Request object that had failed validation
        :param serializer: (rest_framework.serializers.Serializer) Serializer object that rejected the request
        """

        # Filter HTTP headers from request metadata
        request_headers = request.META
        http_headers = dict([(header, value) for header, value in request_headers.items() if header.startswith('HTTP')])
        cleaned_headers = self._clean_headers(copy.deepcopy(http_headers))

        request_data = {
            'params': request.GET,
            'data': request.data,
            'user_id': request.user.id,
            'headers': cleaned_headers,
            'method': request.method,
            'errors': serializer.errors,
            'view': '{}.{}'.format(self.__class__.__module__, self.__class__.__name__),
            'fingerprint': auto_fingerprint('bad_request', **kwargs),
            'trace_id': request.trace_id
        }

        logger.warning(
            'Invalid {} data supplied to {}'.format(request.method, self.__class__.__name__),
            extra=request_data
        )

    def _validate_request(self, request):
        """
        Wrapper around the django-rest-framework serializer validation to validate the
        request data against the serializer class specified for the view.

        Returns True if the request validates against the serializer and sets the
        `cleaned_data` attribute of the request to the validated data,
        or returns False if the request did not meet the serializer requirements.

        Raises an `AttributeError` if the view does not have a serializer for the
        request method.

        :param request: (rest_framework.request.Request) Request object to validate against the view serializer

        :return: (bool)

        :raises: (AttributeError)
        """
        serializer_class = getattr(self, '{}_request_serializer'.format(request.method.lower()), None)

        if serializer_class:
            data = getattr(request, self.REQUEST_DATA_MAPPING[request.method], {})
            self.data = data
            serializer = serializer_class(data=data)

            if serializer.is_valid():
                self.cleaned_data = serializer.data
                return True
            else:
                self._log_bad_request(request, serializer)
                self.errors = serializer.errors
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
            return super().get(request, *args, **kwargs)
        else:
            return BadRequest(data={'errors': self.errors})


class PostRequestValidatorMixin(ValidateRequestDataMixin):
    post_request_serializer = None

    def post(self, request, *args, **kwargs):
        if self._validate_request(request):
            return super().post(request, *args, **kwargs)
        else:
            return BadRequest()


class DeleteRequestValidatorMixin(ValidateRequestDataMixin):
    delete_request_serializer = None

    def delete(self, request, *args, **kwargs):
        if self._validate_request(request):
            return super().delete(request, *args, **kwargs)
        else:
            return BadRequest()


class PatchRequestValidatorMixin(ValidateRequestDataMixin):
    patch_request_serializer = None

    def patch(self, request, *args, **kwargs):
        if self._validate_request(request):
            return super().patch(request, *args, **kwargs)
        else:
            return BadRequest()
