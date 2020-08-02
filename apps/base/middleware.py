from django.http import JsonResponse
from django.urls import resolve


class ShortCircuitMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/tunes'):
            func = resolve(request.path).func
            response = func(request)
            if not isinstance(response, JsonResponse):
                response = JsonResponse(response.data, safe=False)

            return response
        else:
            return self.get_response(request)
