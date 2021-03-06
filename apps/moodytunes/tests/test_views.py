from unittest import mock

from django.test import TestCase
from django.urls import reverse

from libs.tests.helpers import MoodyUtil


class TestBrowsePlaylistsView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.url = reverse('moodytunes:browse')

    def setUp(self):
        self.client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    @mock.patch('tunes.utils.CachedPlaylistManager.retrieve_cached_browse_playlist')
    def test_cached_playlist_exists_is_true_in_context(self, mock_cache_retrieve):
        song = MoodyUtil.create_song()
        mock_cache_retrieve.return_value = [song]

        resp = self.client.get(self.url)
        self.assertTrue(resp.context['cached_playlist_exists'])

    @mock.patch('tunes.utils.CachedPlaylistManager.retrieve_cached_browse_playlist')
    def test_cached_playlist_exists_is_false_in_context(self, mock_cache_retrieve):
        mock_cache_retrieve.return_value = None

        resp = self.client.get(self.url)
        self.assertFalse(resp.context['cached_playlist_exists'])
