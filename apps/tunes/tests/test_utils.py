import random
import string
from unittest import mock

from django.conf import settings
from django.test import TestCase

from accounts.models import UserSongVote
from libs.tests.helpers import MoodyUtil
from tunes.models import Emotion, Song
from tunes.utils import CachedPlaylistManager, filter_duplicate_votes_on_song_from_playlist, generate_browse_playlist


class TestGenerateBrowsePlaylist(TestCase):
    def test_happy_path(self):
        song = MoodyUtil.create_song(valence=.5, energy=.75)
        outlier_song = MoodyUtil.create_song(valence=.25, energy=.30)

        playlist = generate_browse_playlist(song.energy, song.valence, song.danceability)

        self.assertIn(song, playlist)
        self.assertNotIn(outlier_song, playlist)

    def test_jitter_query_uses_boundary_query(self):
        songs_mock = mock.MagicMock()

        energy = .5
        valence = .75
        danceability = .65
        jitter = .2

        generate_browse_playlist(energy, valence, danceability, jitter=jitter, songs=songs_mock)

        energy_lower_limit = energy - jitter
        energy_upper_limit = energy + jitter

        valence_lower_limit = valence - jitter
        valence_upper_limit = valence + jitter

        danceability_lower_limit = danceability - jitter
        danceability_upper_limit = danceability + jitter

        songs_mock.filter.assert_called_once_with(
            energy__range=(energy_lower_limit, energy_upper_limit),
            valence__range=(valence_lower_limit, valence_upper_limit),
            danceability__range=(danceability_lower_limit, danceability_upper_limit),
        )

    def test_no_jitter_query_uses_params_passed(self):
        songs_mock = mock.MagicMock()

        energy = .5
        valence = .75
        danceability = .65

        generate_browse_playlist(energy, valence, danceability, songs=songs_mock)

        songs_mock.filter.assert_called_once_with(
            energy__range=(energy, energy),
            valence__range=(valence, valence),
            danceability__range=(danceability, danceability),
        )

    def test_limit_on_playlist(self):
        energy = .5
        valence = .75
        danceability = .65
        for _ in range(10):
            MoodyUtil.create_song(energy=energy, valence=valence, danceability=danceability)

        playlist = generate_browse_playlist(energy, valence, danceability, limit=5)

        self.assertEqual(len(playlist), 5)

    def test_strategy_passed_filters_only_by_strategy_attribute(self):
        songs_mock = mock.MagicMock()

        energy = .5
        valence = .75
        danceability = .65
        jitter = .2
        strategy = 'energy'

        generate_browse_playlist(energy, valence, danceability, strategy=strategy, jitter=jitter, songs=songs_mock)

        energy_lower_limit = energy - jitter
        energy_upper_limit = energy + jitter

        songs_mock.filter.assert_called_once_with(energy__range=(energy_lower_limit, energy_upper_limit))

    def test_invalid_strategy_passed_raises_exception(self):
        songs_mock = mock.MagicMock()

        energy = .5
        valence = .75
        danceability = .65
        jitter = .2
        strategy = 'invalid'

        with self.assertRaises(ValueError):
            generate_browse_playlist(energy, valence, danceability, strategy=strategy, jitter=jitter, songs=songs_mock)

    def test_artist_passed_only_returns_songs_from_artist(self):
        artist = 'TTK'
        song_params = {
            'energy': .5,
            'valence': .75,
            'danceability': .65,
        }

        song_from_artist = MoodyUtil.create_song(artist=artist, **song_params)
        song_from_other_artist = MoodyUtil.create_song(artist='Bum', **song_params)

        playlist = generate_browse_playlist(
            song_params['energy'],
            song_params['valence'],
            song_params['danceability'],
            jitter=0,
            artist=artist
        )

        self.assertIn(song_from_artist, playlist)
        self.assertNotIn(song_from_other_artist, playlist)

    def test_top_artists_passed_returns_songs_by_top_artists(self):
        top_artists = ['Madlib', 'MF DOOM', 'Surf Curse']
        song_params = {
            'energy': .5,
            'valence': .75,
            'danceability': .65,
        }

        for artist in top_artists:
            MoodyUtil.create_song(artist=artist, **song_params)

        MoodyUtil.create_song(artist='Bum', **song_params)

        expected_playlist = list(Song.objects.filter(artist__in=top_artists))
        playlist = generate_browse_playlist(
            song_params['energy'],
            song_params['valence'],
            song_params['danceability'],
            jitter=0,
            top_artists=top_artists
        )

        # Sort playlists for comparison as the playlist is shuffled
        playlist = list(playlist)
        expected_playlist.sort(key=lambda song: song.code)
        playlist.sort(key=lambda song: song.code)

        self.assertListEqual(expected_playlist, playlist)

    def test_top_artists_passed_returns_default_playlist_if_no_matches_found(self):
        top_artists = ['Madlib', 'MF DOOM', 'Surf Curse']
        song_params = {
            'energy': .5,
            'valence': .75,
            'danceability': .65,
        }

        MoodyUtil.create_song(artist='Bum', **song_params)
        MoodyUtil.create_song(artist='Wack', **song_params)
        MoodyUtil.create_song(artist='Geek', **song_params)

        expected_playlist = list(Song.objects.exclude(artist__in=top_artists))
        playlist = generate_browse_playlist(
            song_params['energy'],
            song_params['valence'],
            song_params['danceability'],
            jitter=0,
            top_artists=top_artists
        )

        # Sort playlists for comparison as the playlist is shuffled
        playlist = list(playlist)
        expected_playlist.sort(key=lambda song: song.code)
        playlist.sort(key=lambda song: song.code)

        self.assertListEqual(expected_playlist, playlist)

    def test_playlist_includes_songs_from_other_artists_if_top_artist_playlist_is_less_than_limit(self):
        top_artists = ['Madlib', 'MF DOOM', 'Surf Curse']
        song_params = {
            'energy': .5,
            'valence': .75,
            'danceability': .65,
        }

        top_artist_song = MoodyUtil.create_song(artist=top_artists[0], **song_params)

        # Create songs from other artists
        for _ in range(10):
            artist = ''.join([random.choice(string.ascii_letters) for _ in range(10)])
            MoodyUtil.create_song(artist=artist, **song_params)

        limit = 5

        playlist = generate_browse_playlist(
            song_params['energy'],
            song_params['valence'],
            song_params['danceability'],
            jitter=0,
            top_artists=top_artists,
            limit=limit
        )

        self.assertEqual(len(playlist), limit)
        self.assertIn(top_artist_song, playlist)


class TestCachedPlaylistManager(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.manager = CachedPlaylistManager(cls.user)

    def test_make_cache_key_returns_expected_cache_key(self):
        expected_cache_key = 'browse:cached-playlist:{}'.format(self.user.username)
        self.assertEqual(self.manager._make_cache_key(), expected_cache_key)

    @mock.patch('tunes.utils.cache')
    def test_cache_browse_playlist_calls_cache_with_expected_arguments(self, mock_cache):
        MoodyUtil.create_song()
        data = {
            'emotion': 'HPY',
            'context': 'WORK',
            'description': '',
            'playlist': Song.objects.all()
        }
        cache_key = 'browse:cached-playlist:{}'.format(self.user.username)
        self.manager.cache_browse_playlist(**data)

        mock_cache.set.assert_called_once_with(cache_key, data, settings.BROWSE_PLAYLIST_CACHE_TIMEOUT)

    @mock.patch('tunes.utils.cache')
    def test_retrieve_cached_playlist_returns_cached_playlist(self, mock_cache):
        MoodyUtil.create_song()
        playlist = Song.objects.all()
        mock_cache.get.return_value = playlist

        returned_playlist = self.manager.retrieve_cached_browse_playlist()
        self.assertEqual(playlist, returned_playlist)

    @mock.patch('tunes.utils.cache')
    def test_retrieve_cached_playlist_returns_None_if_no_playlist_cached(self, mock_cache):
        mock_cache.get.return_value = None

        returned_playlist = self.manager.retrieve_cached_browse_playlist()
        self.assertIsNone(returned_playlist)


class TestFilterDuplicateVotesOnSongs(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.song = MoodyUtil.create_song()
        cls.user = MoodyUtil.create_user()
        cls.emotion = Emotion.objects.get(name=Emotion.HAPPY)

    def test_filter_removes_duplicate_votes_on_song(self):
        MoodyUtil.create_user_song_vote(self.user, self.song, self.emotion, True)
        MoodyUtil.create_user_song_vote(self.user, self.song, self.emotion, True, context='WORK')

        user_votes = UserSongVote.objects.filter(user=self.user, emotion=self.emotion)
        filtered_votes = filter_duplicate_votes_on_song_from_playlist(user_votes)

        self.assertEqual(filtered_votes.count(), 1)

    def test_filter_does_not_remove_different_songs(self):
        other_song = MoodyUtil.create_song()
        MoodyUtil.create_user_song_vote(self.user, self.song, self.emotion, True)
        MoodyUtil.create_user_song_vote(self.user, other_song, self.emotion, True)

        user_votes = UserSongVote.objects.filter(user=self.user, emotion=self.emotion)
        filtered_votes = filter_duplicate_votes_on_song_from_playlist(user_votes)

        self.assertEqual(filtered_votes.count(), 2)

    def test_filter_passed_no_votes_returns_empty_queryset(self):
        user_votes = UserSongVote.objects.filter(user=self.user, emotion=self.emotion)
        filtered_votes = filter_duplicate_votes_on_song_from_playlist(user_votes)

        self.assertEqual(filtered_votes.count(), 0)
