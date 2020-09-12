import coreapi
from django.test import TestCase
from rest_framework import serializers

from base.utils import build_documentation_for_request_serializer


class TestRequestSerializer(serializers.Serializer):
    foo = serializers.CharField(help_text='Test Char Field')
    bar = serializers.IntegerField(required=False, help_text='Test Int Field')


class TestBuildDocumentationForRequestSerializer(TestCase):
    def test_build_docs(self):
        location = 'query'

        expected_foo_schema = coreapi.Field(
            'foo',
            required=True,
            location=location,
            type='string',
            description='Test Char Field'
        )

        expected_bar_schema = coreapi.Field(
            'bar',
            required=False,
            location=location,
            type='integer',
            description='Test Int Field'
        )

        schema = build_documentation_for_request_serializer(TestRequestSerializer, location)
        fields = schema._manual_fields

        self.assertEqual(fields[0], expected_foo_schema)
        self.assertEqual(fields[1], expected_bar_schema)
