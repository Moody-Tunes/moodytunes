import coreapi
import rest_framework
from rest_framework.schemas import AutoSchema

import base


def build_documentation_for_request_serializer(serializer_class, location):
    """
    Generate a list of coreapi Fields for use in documenting a django-rest-framework API view.
    The return value of this function should be set as the view schema field.

    :param serializer_class: (serializers.Serializer) django-rest-framework serializer for validating request data
    :param location: (str) Method used for the requests to this view. Should be one of [path, query, form, body]

    :return: (list(coreapi.Field))
    """
    serializer = serializer_class()
    serializer_fields = [f for f in serializer.fields.items()]
    fields = []

    field_class_to_type_map = {
        base.fields.CleanedChoiceField: 'string',
        rest_framework.fields.CharField: 'string',
        rest_framework.fields.FloatField: 'float',
        rest_framework.fields.IntegerField: 'integer'
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
