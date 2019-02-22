from unittest import mock

from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

from base.mixins import ValidateRequestDataMixin
from libs.tests.helpers import MoodyUtil


class TestValidateRequestDataMixing(TestCase):
    def setUp(self):
        self.mixin = ValidateRequestDataMixin()
        self.factory = APIRequestFactory()
        self.user = MoodyUtil.create_user()

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

    @mock.patch('base.mixins.logger')
    def test_log_bad_request(self, mock_logger):
        mock_serializer = mock.Mock()
        mock_serializer.errors = 'Some bad data here'

        request = self.factory.get(
            '/test/',
            data={'foo': 'bar'},
            HTTP_COOKIE='sesssionid=foobarbaz',
            HTTP_HOST='example.com'
        )
        request.user = self.user
        request.data = ''

        expected_request_data = {
            'params': request.GET,
            'data': request.data.encode(),
            'user_id': request.user.id,
            'headers': {
                'HTTP_HOST': 'example.com',
                'HTTP_COOKIE': '********'
            },
            'method': request.method,
            'errors': mock_serializer.errors
        }

        self.mixin._log_bad_request(request, mock_serializer)
        mock_logger.warning.assert_called_once_with(
            'Invalid {} data supplied to {}'.format(request.method, self.mixin.__class__.__name__),
            extra=expected_request_data
        )

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
        mock_bad_request_logger.assert_called_once_with(request, mock_serializer)
