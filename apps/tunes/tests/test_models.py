from django.core.exceptions import ValidationError
from django.test import TestCase

from tunes.models import Emotion, Song


class TestEmotion(TestCase):
    @classmethod
    def setUpTestData(cls):
        # First we need to delete all Emotions, so we can create our own for
        # testing purposes. Hard to create new Emotions with the uniqueness and
        # choice lock on the model
        Emotion.objects.all().delete()

    def test_invalid_choice(self):
        with self.assertRaises(ValidationError):
            Emotion.objects.create(
                name='Im Not Real!',
                energy=.5,
                valence=.5,
            )

    def test_invalid_boundary_negative(self):
        with self.assertRaises(ValidationError):
            Emotion.objects.create(
                name=Emotion.HAPPY,
                energy=-.5,
                valence=.5,
            )

    def test_invalid_boundary_beyond_range(self):
        with self.assertRaises(ValidationError):
            Emotion.objects.create(
                name=Emotion.HAPPY,
                energy=2,
                valence=.5,
            )

    def test_uniqueness_on_name(self):
        Emotion.objects.create(
            name=Emotion.HAPPY,
            energy=.5,
            valence=.5
        )

        with self.assertRaises(ValidationError):
            Emotion.objects.create(
                name=Emotion.HAPPY,
                energy=.5,
                valence=.5
            )

    def test_get_full_name_from_keyword_happy_path(self):
        name = 'MEL'
        expected_fullname = 'Melancholy'

        self.assertEqual(Emotion.get_full_name_from_keyword(name), expected_fullname)

    def test_get_full_name_returns_none_for_invalid_name(self):
        name = 'foo'

        self.assertIsNone(Emotion.get_full_name_from_keyword(name))


class TestSong(TestCase):

    def test_invalid_boundary_negative(self):
        with self.assertRaises(ValidationError):
            Song.objects.create(
                artist='J-Dilla',
                name='Donuts',
                code='spotify:track:something-or-other',
                valence=-.5,
                energy=-.5
            )

    def test_invalid_boundary_beyond_range(self):
        with self.assertRaises(ValidationError):
            Song.objects.create(
                artist='J-Dilla',
                name='Donuts',
                code='spotify:track:something-or-other',
                valence=2,
                energy=5
            )

    def test_uniqueness_on_code(self):
        song_code = 'spotify:track:something-or-other'

        Song.objects.create(
            artist='J-Dilla',
            name='Donuts',
            code=song_code,
            valence=.5,
            energy=.5
        )

        with self.assertRaises(ValidationError):
            Song.objects.create(
                artist='J-Dilla',
                name='Waves',
                code=song_code,
                valence=.5,
                energy=.5
            )
