from django.core.exceptions import ValidationError
from django.test import TestCase

from tunes.models import Emotion, Song


class TestEmotion(TestCase):
    @classmethod
    def setUpTestData(cls):
        # First we need to delete all Emotions, so we can create our own for
        # testing purposes. Hard to create new Emotions with the uniquness and
        # choice lock on the model
        Emotion.objects.all().delete()

    def test_invalid_choice(self):
        with self.assertRaises(ValidationError):
            Emotion.objects.create(
                name='Im Not Real!',
                upper_bound=.5,
                lower_bound=.5,
            )

    def test_invalid_boundary_negative(self):
        with self.assertRaises(ValidationError):
            Emotion.objects.create(
                name=Emotion.HAPPY,
                upper_bound=-.5,
                lower_bound=.5,
            )

    def test_invalid_boundary_beyond_range(self):
        with self.assertRaises(ValidationError):
            Emotion.objects.create(
                name=Emotion.HAPPY,
                upper_bound=2,
                lower_bound=.5,
            )

    def test_uniqueness_on_name(self):
        Emotion.objects.create(
            name=Emotion.HAPPY,
            upper_bound=.5,
            lower_bound=.5
        )

        with self.assertRaises(ValidationError):
            Emotion.objects.create(
                name=Emotion.HAPPY,
                upper_bound=.5,
                lower_bound=.5
            )


class TestSong(TestCase):
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
