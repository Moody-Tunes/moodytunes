import coreapi
from django.test import TestCase
from rest_framework import serializers

from base.documentation_utils import MultipleMethodSchema, build_documentation_for_request_serializer


class DummyRequestSerializer(serializers.Serializer):
    foo = serializers.CharField(help_text='Test Char Field')
    bar = serializers.IntegerField(required=False, help_text='Test Int Field')


class DummyPostRequestSerializer(serializers.Serializer):
    biz = serializers.BooleanField(help_text='Test Boolean Field')
    baz = serializers.IntegerField(required=False, help_text='Test Int Field')


class DummyDeleteRequestSerializer(serializers.Serializer):
    flim = serializers.CharField(help_text='Test Char Field')
    flam = serializers.BooleanField(required=False, help_text='Test Boolean Field')


class DummyPatchRequestSerializer(serializers.Serializer):
    hey = serializers.IntegerField(help_text='Test Integer Field')
    oh = serializers.BooleanField(required=False, help_text='Test Boolean Field')


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
        cls.get_request_serializer = DummyRequestSerializer
        cls.post_request_serializer = DummyPostRequestSerializer
        cls.delete_request_serializer = DummyDeleteRequestSerializer
        cls.patch_request_serializer = DummyPatchRequestSerializer

        cls.schema_instance = MultipleMethodSchema(
            get_request_serializer=cls.get_request_serializer,
            post_request_serializer=cls.post_request_serializer,
            delete_request_serializer=cls.delete_request_serializer,
            patch_request_serializer=cls.patch_request_serializer
        )

    def test_get_manual_fields_for_get_request_returns_get_serializer_fields(self):
        schema = build_documentation_for_request_serializer(self.get_request_serializer, 'query')
        expected_fields = schema._manual_fields
        fields = self.schema_instance.get_manual_fields('/', 'GET')

        self.assertEqual(fields, expected_fields)

    def test_get_manual_fields_for_post_request_returns_post_serializer_fields(self):
        schema = build_documentation_for_request_serializer(self.post_request_serializer, 'form')
        expected_fields = schema._manual_fields
        fields = self.schema_instance.get_manual_fields('/', 'POST')

        self.assertEqual(fields, expected_fields)

    def test_get_manual_fields_for_delete_request_returns_delete_serializer_fields(self):
        schema = build_documentation_for_request_serializer(self.delete_request_serializer, 'form')
        expected_fields = schema._manual_fields
        fields = self.schema_instance.get_manual_fields('/', 'DELETE')

        self.assertEqual(fields, expected_fields)

    def test_get_manual_fields_for_patch_request_returns_patch_serializer_fields(self):
        schema = build_documentation_for_request_serializer(self.patch_request_serializer, 'form')
        expected_fields = schema._manual_fields
        fields = self.schema_instance.get_manual_fields('/', 'PATCH')

        self.assertEqual(fields, expected_fields)
