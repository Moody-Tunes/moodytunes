from django.shortcuts import reverse
from django.test import TestCase


class TestAddTraceIdToRequestMiddleware(TestCase):
    def test_trace_id_is_set_for_request(self):
        url = reverse('accounts:login')
        response = self.client.get(url)

        self.assertTrue(hasattr(response.wsgi_request, 'trace_id'))
