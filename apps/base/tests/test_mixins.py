from unittest import mock

from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

from base.mixins import ValidateRequestDataMixin


class TestValidateRequestDataMixing(TestCase):
    def setUp(self):
        self.mixin = ValidateRequestDataMixin()
        self.factory = APIRequestFactory()

    def test_clean_headers_does_not_strip_safe_values(self):
        headers = {'HTTP_HOST': 'example.com'}
        new_header = self.mixin._clean_headers(headers)
        self.assertEqual(new_header['HTTP_HOST'], headers['HTTP_HOST'])

    def test_clean_headers_with_authorization_header(self):
        headers = {'HTTP_AUTHORIZATION': 'Foo-Bar'}
        new_headers = self.mixin._clean_headers(headers)
        self.assertEqual(new_headers['HTTP_AUTHORIZATION'], '********')

    def test_clean_headers_with_sessionid(self):
        headers = {'HTTP_COOKIE': 'sessionid=foobarbaz'}
        new_headers = self.mixin._clean_headers(headers)
        self.assertEqual(new_headers['HTTP_COOKIE'], '********')

    def test_serializer_not_specified_raises_attribute_error(self):
        request = self.factory.get('/test/')

        with self.assertRaises(AttributeError):
            self.mixin._validate_request(request)

    def test_valid_data_sets_mixin_cleaned_data(self):
        request_data = {'foo': 'bar'}

        mock_serializer = mock.Mock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = request_data
        mock_serializer.return_value = mock_serializer

        mixin = ValidateRequestDataMixin()
        mixin.get_request_serializer = mock_serializer

        mock_request = self.factory.get('/test/', data=request_data)
        request = Request(mock_request)
        resp = mixin._validate_request(request)

        self.assertTrue(resp)
        self.assertDictEqual(mixin.cleaned_data, request_data)

    @mock.patch('base.mixins.ValidateRequestDataMixin._log_bad_request')
    def test_invalid_data_logs_bad_request(self, mock_bad_request_logger):
        request_data = {'foo': 'bar'}

        mock_serializer = mock.Mock()
        mock_serializer.is_valid.return_value = False
        mock_serializer.return_value = mock_serializer

        mixin = ValidateRequestDataMixin()
        mixin.get_request_serializer = mock_serializer

        mock_request = self.factory.get('/test/', data=request_data)
        request = Request(mock_request)
        resp = mixin._validate_request(request)

        self.assertFalse(resp)
        mock_bad_request_logger.assert_called_once_with(request)
