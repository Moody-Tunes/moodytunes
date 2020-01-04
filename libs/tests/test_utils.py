from django.test import TestCase

from tunes.models import Song
from libs.utils import average
from libs.tests.helpers import MoodyUtil


class TestAverage(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.song_1 = MoodyUtil.create_song(energy=.5, valence=.75)
        cls.song_2 = MoodyUtil.create_song(energy=.65, valence=.45)

    def test_average_computes_proper_average_for_attribute(self):
        collection = Song.objects.all()
        expected_valence = .6
        expected_energy = .57

        calculated_valence = average(collection, 'valence')
        self.assertEqual(calculated_valence, expected_valence)

        calculated_energy = average(collection, 'energy')
        self.assertEqual(calculated_energy, expected_energy)

    def test_empty_queryset_returns_null(self):
        collection = Song.objects.none()

        calculated_average = average(collection, 'valence')
        self.assertIsNone(calculated_average)

    def test_invalid_attribute_rasies_exception(self):
        collection = Song.objects.all()

        with self.assertRaises(ValueError):
            average(collection, 'foo')
