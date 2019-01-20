from unittest import mock

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from base.mixins import ValidateRequestDataMixin


class TestValidateRequestDataMixing(TestCase):
    def setUp(self):
        self.mixin = ValidateRequestDataMixin()
        self.mixin.get = None  # Need to mock at least one method for the view
        self.factory = APIRequestFactory()

    def test_dispatch_with_no_form_provided_raises_validation_error(self):
        mock_request = self.factory.get('/path/')

        with self.assertRaises(AttributeError):
            self.mixin.dispatch(mock_request)

    @mock.patch('rest_framework.generics.GenericAPIView.dispatch')
    def test_dispatch_happy_path(self, super_dispatch):
        transformed_data = {'hello': 'world'}

        mock_serializer = mock.MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = transformed_data
        mock_serializer.return_value = mock_serializer
        self.mixin.get_request_serializer = mock_serializer

        mock_request = self.factory.get('/path/', data=transformed_data)

        self.mixin.dispatch(mock_request)
        super_dispatch.assert_called_once_with(mock_request)
        self.assertDictEqual(self.mixin.cleaned_data, transformed_data)

    def test_dispatch_receives_invalid_data(self):
        transformed_data = {'hello': 'world'}

        mock_serializer = mock.MagicMock()
        mock_serializer.is_valid.return_value = False
        mock_serializer.return_value = mock_serializer
        self.mixin.get_request_serializer = mock_serializer

        mock_request = self.factory.get('/path/', data=transformed_data)

        with mock.patch.object(self.mixin, '_handle_bad_request') as error_handler:
            error_handler.return_value = None
            self.mixin.dispatch(mock_request)

            error_handler.assert_called_once_with(mock_request)
            self.assertIsNone(self.mixin.response)

    def test_dispatch_receives_method_not_allowed(self):
        # Test mixin only has GET method
        mock_request = self.factory.post('/path/', data={'mock_data': 'foo-bar'})

        with mock.patch.object(self.mixin, '_log_bad_request') as error_logger:
            resp = self.mixin.dispatch(mock_request)

            error_logger.assert_called_once_with()
            self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
            self.assertEqual(resp['Allow'], ', '.join(self.mixin.allowed_methods))
