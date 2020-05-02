from rest_framework import status
from rest_framework.response import Response


class BadRequest(Response):
    status_code = status.HTTP_400_BAD_REQUEST
