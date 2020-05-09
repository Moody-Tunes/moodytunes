from unittest import mock

from django.test import TestCase

from libs.tests.helpers import MoodyUtil
from moodytunes.forms import BrowseForm, PlaylistForm, SuggestSongForm, get_genre_choices
from tunes.models import Emotion


class TestGetGenreChoices(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.default_choice = ('', '-----------')

    def test_method_returns_all_song_genres(self):
        hiphop_song = MoodyUtil.create_song(genre='hiphop')
        rock_song = MoodyUtil.create_song(genre='rock')

        expected_choices = [
            self.default_choice,
            (hiphop_song.genre, hiphop_song.genre),
            (rock_song.genre, rock_song.genre)
        ]

        choices = get_genre_choices()

        self.assertEqual(choices, expected_choices)

    def test_method_returns_genres_for_songs_user_upvoted(self):
        user = MoodyUtil.create_user()
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        upvoted_song = MoodyUtil.create_song(genre='hiphop')
        downvoted_song = MoodyUtil.create_song(genre='rock')

        MoodyUtil.create_user_song_vote(user, upvoted_song, emotion, True)
        MoodyUtil.create_user_song_vote(user, downvoted_song, emotion, False)

        expected_choices = [
            self.default_choice,
            (upvoted_song.genre, upvoted_song.genre),
        ]

        choices = get_genre_choices(user=user)

        self.assertEqual(choices, expected_choices)

    def test_method_omits_empty_genre(self):
        song_with_genre = MoodyUtil.create_song(genre='hiphop')
        MoodyUtil.create_song(genre='')

        expected_choices = [
            self.default_choice,
            (song_with_genre.genre, song_with_genre.genre),
        ]

        choices = get_genre_choices()

        self.assertEqual(choices, expected_choices)

    @mock.patch('tunes.models.Song.objects.all')
    @mock.patch('django.core.cache.cache.get')
    def test_method_uses_cached_return_value_if_present(self, mock_cache, mock_song_lookup):
        genres = ['foo']
        mock_cache.return_value = genres

        expected_genres = [('', '-----------'), ('foo', 'foo')]
        returned_genres = get_genre_choices()

        self.assertEqual(returned_genres, expected_genres)
        mock_song_lookup.assert_not_called()


class TestBrowseForm(TestCase):
    def test_valid_emotion_is_valid(self):
        data = {'emotion': Emotion.HAPPY}
        form = BrowseForm(data)

        self.assertTrue(form.is_valid())

    def test_invalid_emotion_is_invalid(self):
        data = {'emotion': 'it-be-like-that-sometimes'}
        form = BrowseForm(data)

        self.assertFalse(form.is_valid())

    def test_valid_context_is_valid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'context': 'WORK'
        }

        form = BrowseForm(data)
        self.assertTrue(form.is_valid())

    def test_invalid_context_is_invalid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'context': 'PLAY'
        }

        form = BrowseForm(data)
        self.assertFalse(form.is_valid())

    def test_genre_for_song_in_system_is_valid(self):
        song = MoodyUtil.create_song()
        data = {
            'emotion': Emotion.HAPPY,
            'genre': song.genre
        }

        form = BrowseForm(data)
        self.assertTrue(form.is_valid())

    def test_fake_genre_is_not_valid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'genre': 'something-fake'
        }

        form = BrowseForm(data)
        self.assertFalse(form.is_valid())


class TestPlaylistForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()

    def test_valid_emotion_is_valid(self):
        data = {'emotion': Emotion.HAPPY}
        form = PlaylistForm(data, user=self.user)

        self.assertTrue(form.is_valid())

    def test_invalid_emotion_is_invalid(self):
        data = {'emotion': 'it-be-like-that-sometimes'}
        form = PlaylistForm(data, user=self.user)

        self.assertFalse(form.is_valid())

    def test_valid_context_is_valid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'context': 'WORK'
        }

        form = PlaylistForm(data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_invalid_context_is_invalid(self):
        data = {
            'emotion': Emotion.HAPPY,
            'context': 'PLAY'
        }

        form = PlaylistForm(data, user=self.user)
        self.assertFalse(form.is_valid())

    def test_genre_for_voted_song_is_valid(self):
        song = MoodyUtil.create_song()
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        MoodyUtil.create_user_song_vote(self.user, song, emotion, True)

        data = {
            'emotion': Emotion.HAPPY,
            'genre': song.genre
        }

        form = PlaylistForm(data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_genre_not_in_votes_is_not_valid(self):
        song = MoodyUtil.create_song()
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        MoodyUtil.create_user_song_vote(self.user, song, emotion, True)

        data = {
            'emotion': Emotion.HAPPY,
            'genre': 'some-other-genre'
        }

        form = PlaylistForm(data, user=self.user)
        self.assertFalse(form.is_valid())


class TestSuggestSongForm(TestCase):
    def test_valid_data(self):
        data = {'code': 'spotify:track:6JVU5TollB4mTzMkb5d8Z9'}
        form = SuggestSongForm(data)

        self.assertTrue(form.is_valid())

    def test_suggestion_for_existing_song_is_invalid(self):
        song = MoodyUtil.create_song()

        data = {'code': song.code}
        form = SuggestSongForm(data)

        self.assertFalse(form.is_valid())

    def test_invalid_song_code_is_invalid(self):
        data = {'code': 'some-fake-code'}
        form = SuggestSongForm(data)

        self.assertFalse(form.is_valid())
