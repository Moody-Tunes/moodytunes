from django.test import TestCase

from tunes.models import Song
from libs.utils import average
from libs.tests.helpers import MoodyUtil


class TestAverage(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.song_1 = MoodyUtil.create_song(energy=.5, valence=.75, danceability=.5)
        cls.song_2 = MoodyUtil.create_song(energy=.65, valence=.45, danceability=.75)

    def test_average_computes_proper_average_for_citeria(self):
        collection = Song.objects.all()
        expected_valence = .6
        expected_energy = .57
        expected_danceability = .62

        calculated_attrs = average(collection, 'valence', 'energy', 'danceability')

        self.assertEqual(calculated_attrs['valence__avg'], expected_valence)
        self.assertEqual(calculated_attrs['energy__avg'], expected_energy)
        self.assertEqual(calculated_attrs['danceability__avg'], expected_danceability)

    def test_empty_queryset_returns_null_values(self):
        collection = Song.objects.none()

        calculated_attrs = average(collection, 'valence', 'energy', 'danceability')

        self.assertIsNone(calculated_attrs['valence__avg'])
        self.assertIsNone(calculated_attrs['energy__avg'])
        self.assertIsNone(calculated_attrs['danceability__avg'])

    def test_invalid_attribute_raises_exception(self):
        collection = Song.objects.all()

        with self.assertRaises(ValueError):
            average(collection, 'foo')

    def test_set_precision_returns_average_to_desired_precision(self):
        collection = Song.objects.all()
        expected_valence = .6
        expected_energy = .575
        expected_danceability = .625

        calculated_attrs = average(collection, 'valence', 'energy', 'danceability', precision=3)

        self.assertEqual(calculated_attrs['valence__avg'], expected_valence)
        self.assertEqual(calculated_attrs['energy__avg'], expected_energy)
        self.assertEqual(calculated_attrs['danceability__avg'], expected_danceability)
