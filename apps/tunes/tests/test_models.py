from django.core.exceptions import ValidationError
from django.test import TestCase

from tunes.models import Emotion


class TestEmotion(TestCase):
    @classmethod
    def setUpTestData(cls):
        # First we need to delete all Emotions, so we can create our own for
        # testing purposes. Hard to create new Emotions with the uniquness and
        # choice lock on the model
        Emotion.objects.all().delete()

    def test_invalid_choice(self):
        with self.assertRaises(ValidationError):
            emotion = Emotion.objects.create(
                name='Im Not Real!',
                upper_bound=.5,
                lower_bound=.5,
            )

    def test_invalid_boundary_negative(self):
        with self.assertRaises(ValidationError):
            emotion = Emotion.objects.create(
                name=Emotion.HAPPY,
                upper_bound=-.5,
                lower_bound=.5,
            )

    def test_invalid_boundary_beyond_range(self):
        with self.assertRaises(ValidationError):
            emotion = Emotion.objects.create(
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
