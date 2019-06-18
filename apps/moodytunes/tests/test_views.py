from unittest import mock

from django.test import TestCase
from django.urls import reverse

from accounts.models import UserSuggestedSong
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


class TestSuggestSongView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.url = reverse('moodytunes:suggest')

    def setUp(self):
        self.client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    def test_valid_request_saves_suggestion(self):
        code = 'spotify:track:09O91GIt6HRLhgKnlkzjEi'
        data = {'code': code}
        self.client.post(self.url, data=data)

        self.assertTrue(UserSuggestedSong.objects.filter(code=code).exists())

    def test_request_with_existing_code_does_not_add_suggestion(self):
        song = MoodyUtil.create_song()
        data = {'code': song.code}
        self.client.post(self.url, data=data)

        self.assertFalse(UserSuggestedSong.objects.filter(code=song.code).exists())

    def test_request_with_suggested_song_does_not_create_duplicates(self):
        code = 'spotify:track:09O91GIt6HRLhgKnlkzjEi'
        UserSuggestedSong.objects.create(user=self.user, code=code)

        data = {'code': code}
        self.client.post(self.url, data=data)

        self.assertEqual(UserSuggestedSong.objects.filter(code=code).count(), 1)
