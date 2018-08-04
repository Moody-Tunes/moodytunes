from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from base.models import BaseModel


class Emotion(BaseModel):
    """

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
