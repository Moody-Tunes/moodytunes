from django.test import TestCase

from moodytunes.utils import ExportPlaylistHelper
from tunes.models import Emotion
from libs.tests.helpers import MoodyUtil


class TestExportPlaylistHelper(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.song = MoodyUtil.create_song()
        cls.emotion = Emotion.objects.get(name=Emotion.HAPPY)

    def test_happy_path(self):
        MoodyUtil.create_user_song_vote(self.user, self.song, self.emotion, True)
        songs = ExportPlaylistHelper.get_export_playlist_for_user(self.user, self.emotion.name)

        self.assertIn(self.song.code, songs)

    def test_exclude_downvoted_songs(self):
        MoodyUtil.create_user_song_vote(self.user, self.song, self.emotion, False)
        songs = ExportPlaylistHelper.get_export_playlist_for_user(self.user, self.emotion.name)

        self.assertNotIn(self.song.code, songs)

    def test_filter_by_genre(self):
        genre = 'hiphop'
        other_song = MoodyUtil.create_song(genre=genre)

        MoodyUtil.create_user_song_vote(self.user, self.song, self.emotion, True)
        MoodyUtil.create_user_song_vote(self.user, other_song, self.emotion, True)

        songs = ExportPlaylistHelper.get_export_playlist_for_user(self.user, self.emotion.name, genre=other_song.genre)

        self.assertIn(other_song.code, songs)
        self.assertNotIn(self.song.code, songs)

    def test_filter_by_context(self):
        other_song = MoodyUtil.create_song()

        MoodyUtil.create_user_song_vote(self.user, self.song, self.emotion, True, context='WORK')
        MoodyUtil.create_user_song_vote(self.user, other_song, self.emotion, True, context='PARTY')

        songs = ExportPlaylistHelper.get_export_playlist_for_user(self.user, self.emotion.name, context='PARTY')

        self.assertIn(other_song.code, songs)
        self.assertNotIn(self.song.code, songs)