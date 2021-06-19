from django.shortcuts import reverse
from django.test import TestCase


class TestAddTraceIdToRequestMiddleware(TestCase):
    def test_trace_id_is_set_for_request(self):
        url = reverse('accounts:login')
        response = self.client.get(url)

        self.assertTrue(hasattr(response.wsgi_request, 'trace_id'))

    def test_request_with_trace_header_sets_request_trace_id_to_header_value(self):
        trace_id = 'test-trace-id'
        url = reverse('accounts:login')
        response = self.client.get(url, HTTP_X_TRACE_ID=trace_id)

        self.assertEqual(response.wsgi_request.trace_id, trace_id)
