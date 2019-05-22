from unittest import mock

from django.test import TestCase

from tunes.utils import generate_browse_playlist
from libs.tests.helpers import MoodyUtil


class TestGenerateBrowsePlaylist(TestCase):
    def test_happy_path(self):
        song = MoodyUtil.create_song(valence=.5, energy=.75)
        outlier_song = MoodyUtil.create_song(valence=.25, energy=.30)

        playlist = generate_browse_playlist(song.energy, song.valence)

        self.assertIn(song, playlist)
        self.assertNotIn(outlier_song, playlist)

    def test_jitter_query_uses_boundary_query(self):
        songs_mock = mock.MagicMock()

        energy = .5
        valence = .75
        jitter = .2

        energy_lower_limit = energy_upper_limit = energy
        valence_lower_limit = valence_upper_limit = valence

        generate_browse_playlist(energy, valence, jitter=jitter, songs=songs_mock)

        energy_lower_limit -= jitter
        energy_upper_limit += jitter

        valence_lower_limit -= jitter
        valence_upper_limit += jitter

        songs_mock.filter.assert_called_once_with(
            energy__gte=energy_lower_limit,
            energy__lte=energy_upper_limit,
            valence__gte=valence_lower_limit,
            valence__lte=valence_upper_limit
        )

    def test_no_jitter_query_use_params_passed(self):
        songs_mock = mock.MagicMock()

        energy = .5
        valence = .75

        generate_browse_playlist(energy, valence, songs=songs_mock)

        songs_mock.filter.assert_called_once_with(
            energy__gte=energy,
            energy__lte=energy,
            valence__gte=valence,
            valence__lte=valence
        )

    def test_limit_on_playlist(self):
        energy = .5
        valence = .75
        for _ in range(10):
            MoodyUtil.create_song(energy=energy, valence=valence)

        playlist = generate_browse_playlist(energy, valence, limit=5)

        self.assertEqual(len(playlist), 5)
