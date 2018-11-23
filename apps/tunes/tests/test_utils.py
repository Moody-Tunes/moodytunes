from unittest import mock

from django.test import TestCase

from tunes.utils import generate_browse_playlist
from libs.tests.helpers import MoodyUtil


class TestGenerateBrowsePlaylist(TestCase):
    def test_happy_path(self):
        song = MoodyUtil.create_song(valence=.5, energy=.75)
        outlier_song = MoodyUtil.create_song(valence=.25, energy=.30)

        playlist = generate_browse_playlist(song.valence, song.energy)

        self.assertIn(song, playlist)
        self.assertNotIn(outlier_song, playlist)

    def test_exclude_behavior(self):
        in_song = MoodyUtil.create_song(valence=.5, energy=.75)
        out_song = MoodyUtil.create_song(valence=.6, energy=.65)

        playlist = generate_browse_playlist(in_song.valence, in_song.energy, exclude_ids=[out_song.id])

        self.assertIn(in_song, playlist)
        self.assertNotIn(out_song, playlist)

    @mock.patch('tunes.models.Song.objects.filter')
    @mock.patch('random.randint')
    def test_jitter_bumps_upper_bound(self, mock_rand, mock_filter):
        mock_rand.return_value = 2

        lower_bound = .5
        upper_bound = .75
        jitter = .2

        generate_browse_playlist(lower_bound, upper_bound, jitter=jitter)

        expected_lower_bound = lower_bound - jitter
        expected_upper_bound = upper_bound + jitter

        mock_filter.assert_called_with(
            valence__gte=expected_lower_bound,
            valence__lte=expected_upper_bound,
            energy__gte=expected_lower_bound,
            energy__lte=expected_upper_bound
        )

    @mock.patch('tunes.models.Song.objects.filter')
    @mock.patch('random.randint')
    def test_jitter_bumps_lower_bound(self, mock_rand, mock_filter):
        mock_rand.return_value = 1

        lower_bound = .5
        upper_bound = .75
        jitter = .2

        generate_browse_playlist(lower_bound, upper_bound, jitter=jitter)

        expected_lower_bound = lower_bound + jitter
        expected_upper_bound = upper_bound - jitter

        mock_filter.assert_called_with(
            valence__gte=expected_lower_bound,
            valence__lte=expected_upper_bound,
            energy__gte=expected_lower_bound,
            energy__lte=expected_upper_bound
        )

    def test_limit_on_playlist(self):
        for _ in range(10):
            MoodyUtil.create_song(valence=.75, energy=1.0)

        playlist = generate_browse_playlist(.75, 1.0, limit=5)

        self.assertEqual(playlist.count(), 5)
