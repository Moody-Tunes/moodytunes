from unittest import mock
import urllib

from django.test import TestCase
from django.http import QueryDict
from rest_framework.exceptions import ValidationError

from base.mixins import ValidateRequestDataMixin


class TestValidateRequestDataMixing(TestCase):
    def setUp(self):
        self.mixin = ValidateRequestDataMixin()

    def test_parse_request_body_happy_path(self):
        data =  b"{'test': 'case'}"
        expected_return = {'test': 'case'}

        ret = self.mixin._parse_request_body(data)
        self.assertDictEqual(ret, expected_return)

    def test_parse_request_body_raises_validation_error_for_wrong_encoding(self):
        data = "{'oops': 'bad'}"

        with mock.patch.object(self.mixin, '_log_bad_request') as error_logger:
            with self.assertRaises(ValidationError):
                self.mixin._parse_request_body(data)

                error_logger.assert_called()

    def test_parse_request_body_raises_validation_error_for_bad_json_data(self):
        data = "'oops, bad'"

        with mock.patch.object(self.mixin, '_log_bad_request') as error_logger:
            with self.assertRaises(ValidationError):
                self.mixin._parse_request_body(data)

            error_logger.assert_called_once_with()

    def test_dispatch_with_no_form_provided_raises_validation_error(self):
        mock_request = mock.Mock()
        mock_request.method = 'GET'

        with self.assertRaises(AttributeError):
            self.mixin.dispatch(mock_request)

    @mock.patch('rest_framework.generics.GenericAPIView.dispatch')
    def test_dispatch_happy_path(self, super_dispatch):
        transformed_data = {'hello': 'world'}
        query_string = urllib.parse.urlencode(transformed_data)

        mock_form = mock.MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.cleaned_data = transformed_data
        mock_form.return_value = mock_form
        self.mixin.get_form = mock_form

        mock_request = mock.MagicMock()
        mock_request.method = 'GET'
        mock_request.GET = QueryDict(query_string)

        self.mixin.dispatch(mock_request)
        super_dispatch.assert_called_once_with(mock_request)
        self.assertDictEqual(self.mixin.cleaned_data, transformed_data)

    def test_dispatch_receives_invalid_data(self):
        transformed_data = {'hello': 'world'}
        query_string = urllib.parse.urlencode(transformed_data)

        mock_form = mock.MagicMock()
        mock_form.is_valid.return_value = False
        mock_form.return_value = mock_form
        self.mixin.get_form = mock_form

        mock_request = mock.MagicMock()
        mock_request.method = 'GET'
        mock_request.GET = QueryDict(query_string)

        with mock.patch.object(self.mixin, '_handle_bad_request') as error_handler:
            error_handler.return_value = None
            self.mixin.dispatch(mock_request)

            error_handler.assert_called_once_with(mock_request)
            self.assertIsNone(self.mixin.response)

    def test_dispatch_receives_malformed_request(self):
        self.mixin.get_form = mock.MagicMock()

        mock_request = mock.MagicMock()
        mock_request.method = 'GET'

        with mock.patch.object(self.mixin, '_parse_request_body') as mock_parse:
            mock_parse.side_effect = ValidationError

            with mock.patch.object(self.mixin, '_handle_bad_request') as error_handler:
                error_handler.return_value = None
                self.mixin.dispatch(mock_request)

                error_handler.assert_called_once_with(mock_request)
                self.assertIsNone(self.mixin.response)
