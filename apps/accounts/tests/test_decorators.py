from django.http.response import Http404, HttpResponse
from django.test import RequestFactory, TestCase
from django.utils.decorators import method_decorator
from django.views.generic import View
from rest_framework import status

from accounts.decorators import spotify_auth_required
from libs.tests.helpers import MoodyUtil


REDIRECT_URI = '/foo/'


@method_decorator(spotify_auth_required(REDIRECT_URI),  name='dispatch')
class DummySpotifyAuthRequiredView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse()


@method_decorator(spotify_auth_required(REDIRECT_URI, raise_exc=True),  name='dispatch')
class DummySpotifyAuthRequiredViewWithExcRaise(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse()


class TestSpotifyAuthRequiredDecorator(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_with_auth = MoodyUtil.create_user(username='user-with-auth')
        cls.user_without_auth = MoodyUtil.create_user(username='user-without-auth')
        cls.spotify_auth = MoodyUtil.create_spotify_user_auth(cls.user_with_auth)

        cls.factory = RequestFactory()

    def test_decorator_calls_view_method_for_user_with_spotify_auth(self):
        request = self.factory.get('/bar/')
        request.user = self.user_with_auth

        resp = DummySpotifyAuthRequiredView.as_view()(request)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_decorator_redirects_to_supplied_uri_for_user_without_spotify_auth(self):
        request = self.factory.get('/bar/')
        request.user = self.user_without_auth

        resp = DummySpotifyAuthRequiredView.as_view()(request)

        self.assertEqual(resp.status_code, status.HTTP_302_FOUND)
        self.assertEqual(resp['Location'], REDIRECT_URI)

    def test_decorator_returns_not_found_for_user_without_spotify_auth(self):
        request = self.factory.get('/bar/')
        request.user = self.user_without_auth

        with self.assertRaises(Http404):
            DummySpotifyAuthRequiredViewWithExcRaise.as_view()(request)
