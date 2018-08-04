from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from base.models import BaseModel


class Emotion(BaseModel):
    """
    Represents an "emotion" in the context of our offered moods we allow users
    to select from. `lower_bound` and `upper_bound` are the lowest and highest
    points to select songs from for a given emotion. These values must be
    between 0 <= value <= 1. Emotions MAY overlap with other emotion
    boundaries.

    Emotion.name will be the three character value we store in the database.
    To get the full name of an emotion, use the `full_name` property on an
    instance of Emotion.
    ```
    > happy_record = Emotion.objects.get(name=Emotion.HAPPY)
    > happy_record.name
    >>> 'HPY'
    > happy_record.fullname
    >>> 'Happy'
    ```

    To add another emotion to the list, you'll need three things:
        1) Add constant to class
        MOODY = 'MOD'

        2) Add constant to choices
        EMOTION_NAME_CHOICES = [
            #...
            (MOODY, 'Moody'),
        ]

        3) Generate migration to add option to database
        ./manage.py makemigrations tunes.Emotion
            -> Please change the auto generated name to something more
            insightful. For example, the migration file for this example
            could be xxxx_add_moody_option_to_Emotion.py
    """
    MELANCHOLY = 'MEL'
    CALM = 'CLM'
    HAPPY = 'HPY'
    EXCITED = 'EXC'

    EMOTION_NAME_CHOICES = [
        (MELANCHOLY, 'Melancholy'),
        (CALM, 'Calm'),
        (HAPPY, 'Happy'),
        (EXCITED, 'Excited'),
    ]

    EMOTION_NAME_MAP = {
        MELANCHOLY: 'Melancholy',
        CALM: 'Calm',
        HAPPY: 'Happy',
        EXCITED: 'Excited'
    }

    lower_bound = models.DecimalField(max_digits=3, decimal_places=2)
    upper_bound = models.DecimalField(max_digits=3, decimal_places=2)
    name = models.CharField(
        max_length=3,
        choices=EMOTION_NAME_CHOICES,
        db_index=True,
        unique=True
    )

    def __str__(self):
        return self.full_name

    def __repr__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.full_clean()

        super().save(*args, **kwargs)

    def clean(self, *args, **kwargs):
        # Validate that boundaries are 0 < `value` < 1
        # TODO: Is this the best way to do this?
        if self.lower_bound < 0 or self.lower_bound > 1:
            raise ValidationError(
                {'lower_bound': _('lower_bound must be between 0 and 1')}
            )

        if self.upper_bound < 0 or self.upper_bound > 1:
            raise ValidationError(
                {'upper_bound': _('upper_bound must be between 0 and 1')}
            )

        super().clean(*args, **kwargs)

    @property
    def full_name(self):
        # TODO: Is there a more DRY way to get the full name of the Emotion?
        return self.EMOTION_NAME_MAP.get(self.name)
