from django.db import models

from base.models import BaseModel
from base.validators import validate_decimal_value


class Emotion(BaseModel):
    """
    Represents an "emotion" in the context of our offered moods we allow users
    to select from. `energy` and `valence` are the associated Song attribute
    points to use in suggesting songs for for a given emotion. These values must be
    between 0 <= value <= 1. Emotions MAY overlap with other emotion boundaries.

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

    energy = models.FloatField(validators=[validate_decimal_value])
    valence = models.FloatField(validators=[validate_decimal_value])
    danceability = models.FloatField(validators=[validate_decimal_value], default=0)
    name = models.CharField(
        max_length=3,
        choices=EMOTION_NAME_CHOICES,
        unique=True
    )

    def __str__(self):
        return self.full_name

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.name)

    def save(self, *args, **kwargs):
        self.full_clean()

        super().save(*args, **kwargs)

    @property
    def full_name(self):
        """Return human readable name of emotion"""
        return self.get_name_display()

    @staticmethod
    def get_full_name_from_keyword(name):
        """
        Return the full name of the emotion for the given short name

        :param name: (str) Codename for the emotion, one of EMOTION_NAME_CHOICES

        :return: (str)
        """
        return Emotion.EMOTION_NAME_MAP.get(name)


class Song(BaseModel):
    """
    Represents a song retrieved from the Spotify API. The code attribute is
    the unique identifier for the song in Spotify's database. `sentiment` and
    `energy` are measures of the song's mood, with lower values being more
    negative/down and higher values being more positive/upbeat.
    """
    artist = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    genre = models.CharField(max_length=20, blank=True, default='')
    code = models.CharField(max_length=36, unique=True)
    valence = models.FloatField(validators=[validate_decimal_value])
    energy = models.FloatField(validators=[validate_decimal_value])
    danceability = models.FloatField(validators=[validate_decimal_value], default=0)

    def __str__(self):
        return '{}: {}'.format(self.artist, self.name)

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.code)

    def save(self, *args, **kwargs):
        self.full_clean()

        super().save(*args, **kwargs)
