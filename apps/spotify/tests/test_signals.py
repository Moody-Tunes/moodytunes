from unittest import mock

from django.test import TestCase
from spotify.models import SpotifyAuth

from libs.tests.helpers import MoodyUtil


class TestUpdateSpotifyTopArtistsSignal(TestCase):
    @mock.patch('spotify.signals.on_commit')
    def test_task_is_only_called_on_create(self, mock_on_commit):
        user = MoodyUtil.create_user()
        data = {
            'user': user,
            'spotify_user_id': 'spotify_user',
            'access_token': 'access_token',
            'refresh_token': 'refresh_token'
        }

        auth = SpotifyAuth.objects.create(**data)

        # Because we wrap the task call in the `on_commit` method using a lambda,
        # we lose the reference to the task call itself because it is being called
        # through an anonymous function. Mocking the `on_commit` call to ensure it
        # has the proper number of calls works just as well for our purposes
        mock_on_commit.assert_called_once()

        auth.save()
        self.assertEqual(mock_on_commit.call_count, 1)
