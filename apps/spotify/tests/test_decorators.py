from django.http.response import Http404, HttpResponse
from django.test import RequestFactory, TestCase
from rest_framework import status

from libs.tests.helpers import MoodyUtil
from spotify.decorators import spotify_auth_required


REDIRECT_URI = '/foo/'


@spotify_auth_required(REDIRECT_URI)
def dummy_spotify_auth_required_view(request):
    return HttpResponse()


@spotify_auth_required(REDIRECT_URI, raise_exc=True)
def dummy_spotify_auth_required_raise_exc_view(request):
    return HttpResponse()


class TestSpotifyAuthRequiredDecorator(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_with_auth = MoodyUtil.create_user(username='user-with-auth')
        cls.user_without_auth = MoodyUtil.create_user(username='user-without-auth')
        cls.spotify_auth = MoodyUtil.create_spotify_auth(cls.user_with_auth)

        cls.factory = RequestFactory()

    def test_decorator_calls_view_method_for_user_with_spotify_auth(self):
        request = self.factory.get('/bar/')
        request.user = self.user_with_auth

        resp = dummy_spotify_auth_required_view(request)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(request.spotify_auth.id, self.spotify_auth.id)  # Ensure decorator caches auth on request

    def test_decorator_redirects_to_supplied_uri_for_user_without_spotify_auth(self):
        request = self.factory.get('/bar/')
        request.user = self.user_without_auth

        resp = dummy_spotify_auth_required_view(request)

        self.assertEqual(resp.status_code, status.HTTP_302_FOUND)
        self.assertEqual(resp['Location'], REDIRECT_URI)

    def test_decorator_returns_not_found_for_user_without_spotify_auth(self):
        request = self.factory.get('/bar/')
        request.user = self.user_without_auth

        with self.assertRaises(Http404):
            dummy_spotify_auth_required_raise_exc_view(request)
