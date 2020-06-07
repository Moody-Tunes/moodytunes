from unittest import mock

from django.conf import settings
from django.test import TestCase

from libs.tests.helpers import MoodyUtil
from tunes.models import Song
from tunes.utils import CachedPlaylistManager, generate_browse_playlist


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
            energy__gte=energy_lower_limit,
            energy__lte=energy_upper_limit,
            valence__gte=valence_lower_limit,
            valence__lte=valence_upper_limit,
            danceability__gte=danceability_lower_limit,
            danceability__lte=danceability_upper_limit
        )

    def test_no_jitter_query_uses_params_passed(self):
        songs_mock = mock.MagicMock()

        energy = .5
        valence = .75
        danceability = .65

        generate_browse_playlist(energy, valence, danceability, songs=songs_mock)

        songs_mock.filter.assert_called_once_with(
            energy__gte=energy,
            energy__lte=energy,
            valence__gte=valence,
            valence__lte=valence,
            danceability__gte=danceability,
            danceability__lte=danceability,
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

        songs_mock.filter.assert_called_once_with(
            energy__gte=energy_lower_limit,
            energy__lte=energy_upper_limit,
        )

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

    def test_generate_browse_playlist_returns_user_saved_songs_if_passed(self):
        other_song = MoodyUtil.create_song()
        saved_song = MoodyUtil.create_song()

        user = MoodyUtil.create_user()
        auth = MoodyUtil.create_spotify_user_auth(user)
        auth.saved_songs = [saved_song.code]
        auth.save()

        playlist = generate_browse_playlist(
            saved_song.energy,
            saved_song.valence,
            saved_song.danceability,
            user_auth=auth
        )

        self.assertIn(saved_song, playlist)
        self.assertNotIn(other_song, playlist)

    def test_generate_browse_playlist_returns_lookup_if_no_saved_songs_found(self):
        song = MoodyUtil.create_song(energy=.75, valence=.50, danceability=.65)

        user = MoodyUtil.create_user()
        auth = MoodyUtil.create_spotify_user_auth(user)
        auth.saved_songs = ['spotify:track:123']
        auth.save()

        playlist = generate_browse_playlist(
            song.energy,
            song.valence,
            song.danceability,
            jitter=None,
            user_auth=auth
        )

        self.assertIn(song, playlist)


class TestCachedPlaylistManager(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.manager = CachedPlaylistManager()

    def test_make_cache_key_returns_expected_cache_key(self):
        expected_cache_key = 'browse:{}'.format(self.user.username)
        self.assertEqual(self.manager._make_cache_key(self.user), expected_cache_key)

    @mock.patch('tunes.utils.cache')
    def test_cache_browse_playlist_calls_cache_with_expected_arguments(self, mock_cache):
        MoodyUtil.create_song()
        data = {
            'emotion': 'HPY',
            'context': 'WORK',
            'description': '',
            'playlist': Song.objects.all()
        }
        cache_key = 'browse:{}'.format(self.user.username)
        self.manager.cache_browse_playlist(self.user, **data)

        mock_cache.set.assert_called_once_with(cache_key, data, settings.BROWSE_PLAYLIST_CACHE_TIMEOUT)

    @mock.patch('tunes.utils.cache')
    def test_retrieve_cached_playlist_returns_cached_playlist(self, mock_cache):
        MoodyUtil.create_song()
        playlist = Song.objects.all()
        mock_cache.get.return_value = playlist

        returned_playlist = self.manager.retrieve_cached_browse_playlist(self.user)
        self.assertEqual(playlist, returned_playlist)

    @mock.patch('tunes.utils.cache')
    def test_retrieve_cached_playlist_returns_None_if_no_playlist_cached(self, mock_cache):
        mock_cache.get.return_value = None

        returned_playlist = self.manager.retrieve_cached_browse_playlist(self.user)
        self.assertIsNone(returned_playlist)
