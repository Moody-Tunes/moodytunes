from django.test import TestCase

import requests
from pytest_blockage import MockHttpCall
import urllib.request


class TestBlockage(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = 'https://google.com'

    def test_blockage_using_requests(self):
        with self.assertRaises(MockHttpCall):
            requests.get(self.url)

    def test_blockage_using_urllib(self):
        with self.assertRaises(MockHttpCall):
            urllib.request.urlopen(self.url)
