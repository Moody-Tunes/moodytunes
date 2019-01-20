import logging

from django.http import HttpResponseNotAllowed
from rest_framework import generics

from base.responses import BadRequest

logger = logging.getLogger(__name__)


class MoodyMixin(generics.GenericAPIView):
    """Base class for mixins in mtdj"""


class ValidateRequestDataMixin(MoodyMixin):
    """
    Mixin to verify incoming request data. This class contains logic to validate incoming request data for various
    REST methods.

    To use the functionality for this class, inherit from it and define the relevant form to use in verifying data for
    the specific method. For example, if your view has GET functionality and you want to validate the incoming data,
    you should override the `get_request_serializer` attribute on the class.
    """
    get_form = None
    post_form = None
    delete_form = None

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

    def _log_bad_request(self):
        """Log information about a request if something fails to validate"""
        request_data = {
            'params': self.request.GET,
            'data': self.data if self.data else self.request.body,
            'user_id': self.request.user.id,
            'headers': self.request.META,
            'method': self.request.method,
            'allowed_methods': self.allowed_methods
        }

        logger.warning(
            'Invalid {} data supplied to {}'.format(self.request.method, self.__class__.__name__),
            extra=request_data
        )

    def _handle_bad_request(self, request, *args, **kwargs):
        """
        Handles creating an instance of `base.responses.BadResponse` to return the request.
        Follows mostly the same format as the Django implementation of returning a response.
        :param request: (Request) WSGI request object
        :return: (BadRequest) Instance of response indicating a bad request
        """
        self._log_bad_request()
        response = BadRequest('Invalid {} data supplied to {}'.format(request.method, self.__class__.__name__))
        self.headers = self.default_response_headers
        return self.finalize_response(request, response, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        # Need to covert Django WSGI request to DRF request in order to access request.data
        _request = self.initialize_request(request, *args, **kwargs)

        if not hasattr(self, _request.method.lower()):
            self._log_bad_request()
            return HttpResponseNotAllowed(self.allowed_methods)

        serializer_class = getattr(self, '{}_request_serializer'.format(_request.method.lower()))

        if serializer_class:
            data = getattr(_request, self.REQUEST_DATA_MAPPING[_request.method], {})
            self.data = data
            serializer = serializer_class(data=data)

            if serializer.is_valid():
                self.cleaned_data = serializer.data
                return super().dispatch(request, *args, **kwargs)
            else:
                self.response = self._handle_bad_request(request, *args, **kwargs)
                return self.response
        else:
            raise AttributeError(
                '{} received a {} request but did not defined a form class for this method'.format(
                    self.__class__,
                    _request.method
                )
            )
