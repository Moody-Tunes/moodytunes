from django.test import TestCase
from rest_framework.test import APIRequestFactory

from base.mixins import ValidateRequestDataMixin


class TestValidateRequestDataMixing(TestCase):
    def setUp(self):
        self.mixin = ValidateRequestDataMixin()
        self.factory = APIRequestFactory()

    def test_clean_headers_with_authorization_header(self):
        headers = {'HTTP_AUTHORIZATION': 'Foo-Bar'}
        new_headers = self.mixin._clean_headers(headers)
        self.assertEqual(new_headers['HTTP_AUTHORIZATION'], '********')

    def test_clean_headers_with_sessionid(self):
        headers = {'HTTP_COOKIE': 'sessionid=foobarbaz'}
        new_headers = self.mixin._clean_headers(headers)
        self.assertEqual(new_headers['HTTP_COOKIE'], {'sessionid': '********'})

    def test_serializer_not_specified_raises_attribute_error(self):
        request = self.factory.get('/test/')

        with self.assertRaises(AttributeError):
            self.mixin._validate_request(request)
