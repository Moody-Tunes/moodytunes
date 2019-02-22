from django.test import TestCase

from accounts.models import UserSongVote
from accounts.utils import filter_duplicate_votes_on_song_from_playlist
from tunes.models import Emotion
from libs.tests.helpers import MoodyUtil


class TestFilterDuplicateVotesOnSongs(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.song = MoodyUtil.create_song()
        cls.user = MoodyUtil.create_user()
        cls.emotion = Emotion.objects.get(name=Emotion.HAPPY)

    def test_filter_removes_duplicate_votes_on_song(self):
        UserSongVote.objects.create(
            user=self.user,
            song=self.song,
            emotion=self.emotion,
            vote=True
        )

        UserSongVote.objects.create(
            user=self.user,
            song=self.song,
            emotion=self.emotion,
            vote=True,
            context='WORK'
        )

        user_votes = self.user.get_user_song_vote_records(self.emotion.name)
        filtered_votes = filter_duplicate_votes_on_song_from_playlist(user_votes)

        self.assertEqual(filtered_votes.count(), 1)

    def test_filter_passed_no_votes_returns_empty_queryset(self):
        user_votes = self.user.get_user_song_vote_records(self.emotion.name)
        filtered_votes = filter_duplicate_votes_on_song_from_playlist(user_votes)

        self.assertEqual(filtered_votes.count(), 0)
