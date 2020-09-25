import coreapi
from django.test import TestCase
from rest_framework import serializers

from base.utils import MultipleMethodSchema, build_documentation_for_request_serializer


class DummyRequestSerializer(serializers.Serializer):
    foo = serializers.CharField(help_text='Test Char Field')
    bar = serializers.IntegerField(required=False, help_text='Test Int Field')


class DummyPostRequestSerializer(serializers.Serializer):
    biz = serializers.BooleanField(help_text='Test Boolean Field')
    baz = serializers.IntegerField(required=False, help_text='Test Int Field')


class DummyDeleteRequestSerializer(serializers.Serializer):
    flim = serializers.CharField(help_text='Test Char Field')
    flam = serializers.BooleanField(required=False, help_text='Test Boolean Field')


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

        schema = build_documentation_for_request_serializer(DummyRequestSerializer, location)
        fields = schema._manual_fields

        self.assertEqual(fields[0], expected_foo_schema)
        self.assertEqual(fields[1], expected_bar_schema)


class TestMultipleMethodSchema(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.post_request_serializer = DummyPostRequestSerializer
        cls.delete_request_serializer = DummyDeleteRequestSerializer
        cls.schema_instance = MultipleMethodSchema(DummyPostRequestSerializer, DummyDeleteRequestSerializer)
        cls.location = 'form'

    def test_get_manual_fields_for_post_request_returns_post_serializer_fields(self):
        expected_biz_schema = coreapi.Field(
            'biz',
            required=True,
            location=self.location,
            type='boolean',
            description='Test Boolean Field'
        )

        expected_baz_schema = coreapi.Field(
            'baz',
            required=False,
            location=self.location,
            type='integer',
            description='Test Int Field'
        )

        schema = self.schema_instance.get_manual_fields('/', 'POST')

        self.assertEqual(schema[0], expected_biz_schema)
        self.assertEqual(schema[1], expected_baz_schema)

    def test_get_manual_fields_for_delete_request_returns_delete_serializer_fields(self):
        expected_flim_schema = coreapi.Field(
            'flim',
            required=True,
            location=self.location,
            type='string',
            description='Test Char Field'
        )

        expected_flam_schema = coreapi.Field(
            'flam',
            required=False,
            location=self.location,
            type='boolean',
            description='Test Boolean Field'
        )

        schema = self.schema_instance.get_manual_fields('/', 'DELETE')

        self.assertEqual(schema[0], expected_flim_schema)
        self.assertEqual(schema[1], expected_flam_schema)
