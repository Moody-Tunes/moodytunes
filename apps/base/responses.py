from rest_framework.response import Response
from rest_framework import status


class BadRequest(Response):
    status_code = status.HTTP_400_BAD_REQUEST
