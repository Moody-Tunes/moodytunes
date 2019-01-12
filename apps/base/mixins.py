import json
import logging

from django.conf import settings
from django.http import QueryDict, HttpResponseNotAllowed
from rest_framework import generics
from rest_framework.exceptions import ValidationError

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
    you should override the `get_form` attribute on the class.
    """
    get_form = None
    post_form = None
    delete_form = None

    # Dictionary mapping request method to instance attribute containing data for the request
    REQUEST_DATA_MAPPING = {
        'GET': 'GET',
        'POST': 'POST',
        'DELETE': 'body'
    }

    def __init__(self):
        self.cleaned_data = {}  # Cleaned data for request
        self.data = None  # For cases where data is not attached to request
        super().__init__()

    def _log_bad_request(self):
        request_data = {
            'params': self.request.GET,
            'post': self.request.POST,
            'user_id': self.request.user.id,
            'headers': self.request.META,
            'method': self.request.method,
            'allowed_methods': self.allowed_methods
        }

        if self.data:
            request_data['data'] = self.data

        logger.warning(
            'Invalid {} data supplied to {}'.format(self.request.method, self.__class__.__name__),
            extra=request_data
        )

    def _parse_request_body(self, data):
        try:
            raw_data = data.decode(settings.DEFAULT_CHARSET)
        except AttributeError:
            self._log_bad_request()
            raise ValidationError('Unable to decode request body')

        json_data = raw_data.replace("'", "\"")

        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            self._log_bad_request()
            raise ValidationError('Unable to parse request body')

        self.data = data

        return data

    def _handle_bad_request(self, request, *args, **kwargs):
        self._log_bad_request()
        response = BadRequest('Invalid {} data supplied to {}'.format(request.method, self.__class__.__name__))
        self.headers = self.default_response_headers
        return self.finalize_response(request, response, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(self, request.method.lower()):
            self._log_bad_request()
            return HttpResponseNotAllowed(self.allowed_methods)

        form_class = getattr(self, '{}_form'.format(request.method.lower()))

        if form_class:
            data = getattr(request, self.REQUEST_DATA_MAPPING[request.method])

            if data and not isinstance(data, QueryDict):
                try:
                    data = self._parse_request_body(data)
                except ValidationError:
                    self.response = self._handle_bad_request(request, *args, **kwargs)
                    return self.response

            form_data = data or {}
            form = form_class(form_data)

            if form.is_valid():
                self.cleaned_data = form.cleaned_data
                return super().dispatch(request, *args, **kwargs)
            else:
                self.response = self._handle_bad_request(request, *args, **kwargs)
                return self.response
        else:
            raise AttributeError(
                '{} received a {} request but did not defined a form class for this method'.format(
                    self.__class__,
                    request.method
                )
            )
