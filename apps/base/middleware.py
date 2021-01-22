import uuid


class AddTraceIdToRequestMiddleware(object):
    """Middleware to add a `trace_id` attribute to requests for collating logs"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        trace_id = self.__generate_trace_id()
        request.trace_id = trace_id

        return self.get_response(request)

    def __generate_trace_id(self):
        return uuid.uuid4().hex
