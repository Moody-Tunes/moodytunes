import json
import logging

from django.conf import settings
from django.http import QueryDict
from django.urls import reverse
from django.views.generic.base import RedirectView
from rest_framework import generics, status
from rest_framework.response import Response


logger = logging.getLogger(__name__)


class BadRequest(Response):
    status_code = status.HTTP_400_BAD_REQUEST


class ValidateRequestDataMixin(generics.GenericAPIView):
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
        self.delete_data = None  # Django doesn't handle DELETE data as easily as GET or POST...
        super().__init__()

    def _log_bad_request(self):
        logger.warning(
            'Invalid {} data supplied to {}'.format(self.request.method, self.__class__.__name__),
            extra={
                'params': self.request.GET,
                'data': self.delete_data if self.delete_data else self.request.POST,
                'user': self.request.user.id
            }
        )

    def _parse_request_body(self, data):
        raw_data = data.decode(settings.DEFAULT_CHARSET)
        json_data = raw_data.replace("'", "\"")
        data = json.loads(json_data)

        if self.request.method == 'DELETE':
            self.delete_data = data

        return data

    def _handle_bad_request(self, request, *args, **kwargs):
        self._log_bad_request()
        response = BadRequest('Invalid {} data supplied to {}'.format(request.method, self.__class__.__name__))
        self.headers = self.default_response_headers
        self.response = self.finalize_response(request, response, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        form_class = getattr(self, '{}_form'.format(request.method.lower()))
        data = getattr(request, self.REQUEST_DATA_MAPPING[request.method])

        if data and not isinstance(data, QueryDict):
            data = self._parse_request_body(data)

        if data and form_class:
            form = form_class(data)

            if form.is_valid():
                self.cleaned_data = form.cleaned_data
                return super().dispatch(request, *args, **kwargs)
            else:
                self._handle_bad_request(request, *args, **kwargs)
                return self.response
        else:
            return super().dispatch(request, *args, **kwargs)


class HomePageView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return reverse('accounts:profile')
        return reverse('accounts:login')
