from django.urls import resolve


class ShortCircuitMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/tunes'):
            func = resolve(request.path).func
            response = func(request)
            return response
        else:
            return self.get_response(request)
