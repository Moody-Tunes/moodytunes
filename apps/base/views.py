import logging

from django.urls import reverse
from django.views.generic.base import RedirectView
from rest_framework import generics, status
from rest_framework.response import Response


logger = logging.getLogger(__name__)


class BadRequest(Response):
    status_code = status.HTTP_400_BAD_REQUEST


class ValidateRequestDataMixin(generics.GenericAPIView):
    """
    Mixin to verify incoming request data. This object contains the various REST methods (GET, POST, DELETE) used
    by django-rest-framework and adds validation for incoming request data.

    To use the functionality for this class, inherit from it and define the relevant form to use in verifying data for
    the specific method.
    """
    get_form = None
    post_form = None
    delete_form = None

    def __init__(self):
        self.cleaned_data = {}  # Cleaned data for request
        super().__init__()

    def _log_error(self):
        logger.warning(
            'Invalid {} data supplied to {}'.format(self.request.method, self.__class__.__name__),
            extra={
                'params': self.request.GET,
                'data': self.request.data,
                'user': self.request.user.id
            }
        )

    def get(self, request, *args, **kwargs):
        form_class = getattr(self, 'get_form')
        form = form_class(request.GET)

        if form.is_valid():
            self.cleaned_data = form.cleaned_data
            return super().get(request, *args, **kwargs)

        else:
            self._log_error()
            return BadRequest('Invalid GET data supplied to {}'.format(self.__class__.__name__))

    def post(self, request, *args, **kwargs):
        form_class = getattr(self, 'post_form')
        form = form_class(request.POST)

        if form.is_valid():
            self.cleaned_data = form.cleaned_data

            return super().post(request, *args, **kwargs)

        else:
            self._log_error()
            return BadRequest('Invalid GET data supplied to {}'.format(self.__class__.__name__))

    def delete(self, request, *args, **kwargs):
        form_class = getattr(self, 'delete_form')
        form = form_class(request.data)

        if form.is_valid():
            self.cleaned_data = form.cleaned_data

            return super().delete(request, *args, **kwargs)

        else:
            self._log_error()
            return BadRequest('Invalid GET data supplied to {}'.format(self.__class__.__name__))


class HomePageView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return reverse('accounts:profile')
        return reverse('accounts:login')
