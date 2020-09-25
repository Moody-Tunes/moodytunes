import coreapi
import rest_framework
from rest_framework.schemas import AutoSchema

import base


def build_documentation_for_request_serializer(serializer_class, location):
    """
    Generate an AutoSchema instance for use in documenting a django-rest-framework API view.
    The return value of this function should be set as the view `schema` class attribute.

    :param serializer_class: (serializers.Serializer) django-rest-framework serializer for validating request data
    :param location: (str) Method used for the requests to this view. Should be one of [path, query, form, body]

    :return: (rest_framework.schemas.AutoSchema)
    """
    serializer = serializer_class()
    serializer_fields = [f for f in serializer.fields.items()]
    fields = []

    field_class_to_type_map = {
        base.fields.CleanedChoiceField: 'string',
        rest_framework.fields.CharField: 'string',
        rest_framework.fields.FloatField: 'float',
        rest_framework.fields.IntegerField: 'integer',
        rest_framework.serializers.BooleanField: 'boolean',
    }

    for name, field in serializer_fields:
        fields.append(coreapi.Field(
                name,
                required=field.required,
                location=location,
                type=field_class_to_type_map.get(type(field), 'string'),
                description=field.help_text
            )
        )

    return AutoSchema(manual_fields=fields)


class MultipleMethodSchema(AutoSchema):
    """
    Schema View for API views that handle multiple methods. This schema class will build the fields for
    each method based on the request serializer for the method. To use, set the `schema` class attribute
    for the view to an instance of this class and pass the request serializers to the constructor.
    """

    def __init__(self, post_request_serializer, delete_request_serializer):
        self.post_request_serializer = post_request_serializer
        self.delete_request_serializer = delete_request_serializer

        super().__init__()

    def get_manual_fields(self, path, method):
        extra_fields = []

        if method == 'POST':
            schema = build_documentation_for_request_serializer(self.post_request_serializer, 'form')
            extra_fields = schema._manual_fields
        elif method == 'DELETE':
            schema = build_documentation_for_request_serializer(self.delete_request_serializer, 'form')
            extra_fields = schema._manual_fields

        manual_fields = super().get_manual_fields(path, method)
        return manual_fields + extra_fields
