from logging import getLogger

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from base.models import BaseModel
from base.validators import validate_decimal_value
from libs.moody_logging import auto_fingerprint, update_logging_data
from libs.utils import average
from tunes.models import Song


logger = getLogger(__name__)


class MoodyUser(BaseModel, AbstractUser):
    """
    Represents a user in our system. Extends Django auth features and includes
    logic needed in course of site flow.
    """

    @update_logging_data
    def get_user_emotion_record(self, emotion_name, **kwargs):
        """
        Return the UserEmotion record for a given Emotion name.

        :param emotion_name: (str) `Emotion.name` constant to retrieve

        :return: (UserEmotion)
        """
        try:
            return self.useremotion_set.get(emotion__name=emotion_name)
        except UserEmotion.DoesNotExist:
            logger.warning(
                'User {} has no UserEmotion record for {}'.format(self.username, emotion_name),
                extra={'fingerprint': auto_fingerprint('user_emotion_not_found', **kwargs)}
            )
            return None

    def update_information(self, data):
        """
        Given a dictionary of CLEAN DATA, update the user information accordingly.
        This method must ONLY be used with clean data and should have keys tied to a Django user model
        like username, email, and the like.

        :param data: (dict) Dictionary of data to update for user
        """
        for key, value in data.items():
            # Check that the field exists on the model before updating the attribute, to avoid errors with setting
            # attributes that are not defined for the model.
            if hasattr(self, key):
                setattr(self, key, value)

        self.save()


class UserProfile(BaseModel):
    """
    Stores information about a user in our system. Used to track user preferences for
    our application.
    """
    user = models.OneToOneField(MoodyUser, on_delete=models.CASCADE)
    has_rejected_spotify_auth = models.BooleanField(default=False)
    has_completed_onboarding = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class UserEmotion(BaseModel):
    """
    Represents a mapping between a particular user and an emotion. This allows
    us to store separate attributes for each user for each emotion. Unless
    values are specified upon creation, the attributes will be set to the
    defaults defined in the `Emotion` table.
    """
    user = models.ForeignKey(MoodyUser, on_delete=models.CASCADE)
    emotion = models.ForeignKey('tunes.Emotion', on_delete=models.CASCADE)
    energy = models.FloatField(validators=[validate_decimal_value])
    valence = models.FloatField(validators=[validate_decimal_value])
    danceability = models.FloatField(validators=[validate_decimal_value], default=0)

    class Meta:
        unique_together = ('user', 'emotion')

    def __str__(self):
        return '{} - {}'.format(self.user, self.emotion)

    def save(self, *args, **kwargs):
        self.energy = self.energy or self.emotion.energy
        self.valence = self.valence or self.emotion.valence
        self.danceability = self.danceability or self.emotion.danceability

        self.full_clean()

        super().save(*args, **kwargs)

    def update_attributes(self, candidate_batch_size=None):
        """
        Update the attributes for this user/emotion mapping to the average attributes of the most recent songs
        the user has upvoted as making them feel this emotion. If the user doesn't have any upvotes for this
        emotion, the attributes will be set to `None` and reset to the emotion defaults in the save() call.

        :param candidate_batch_size: (int) Number of songs to include in batch for calculating new attribute values
        """
        if not candidate_batch_size:
            candidate_batch_size = settings.CANDIDATE_BATCH_SIZE_FOR_USER_EMOTION_ATTRIBUTES_UPDATE

        # First, get the distinct upvotes by the user for the emotion.
        # Avoid factoring in a song more than once if there are multiple upvotes for the song
        distinct_votes = self.user.usersongvote_set.filter(
            emotion=self.emotion,
            vote=True
        ).distinct(
            'song__pk',
        ).values_list(
            'pk',
            flat=True
        )

        # Next, get the `candidate_batch_size` most recently distinct songs upvoted for the emotion
        song_pks = UserSongVote.objects.filter(
            pk__in=distinct_votes
        ).order_by(
            '-created'
        ).values_list(
            'song__pk',
            flat=True
        )[:candidate_batch_size]

        # Finally, calculate the average emotion attributes for the songs the user has most
        # recently upvoted for the emotion and set the UserEmotion attributes to the average values
        songs = Song.objects.filter(pk__in=song_pks)
        attributes = average(songs, 'valence', 'energy', 'danceability')

        self.valence = attributes['valence__avg']
        self.energy = attributes['energy__avg']
        self.danceability = attributes['danceability__avg']

        self.save()


class UserSongVote(BaseModel):
    """
    Represents a mapping between a user and a song denoting whether or not the
    song made the user feel the linked emotion. This table will be used to
    track what songs a user associates with a particular emotion.
    """
    CONTEXT_CHOICES = [
        ('', '-----------'),
        ('PARTY', 'Listening to music at a party'),
        ('RELAX', 'Listening to music to relax'),
        ('WORK', 'Listening to music while working on a task'),
        ('EXERCISE', 'Listening to music while exercising'),
        ('OTHER', 'Doing something else')
    ]

    user = models.ForeignKey(MoodyUser, on_delete=models.CASCADE)
    song = models.ForeignKey('tunes.Song', on_delete=models.CASCADE)
    emotion = models.ForeignKey('tunes.Emotion', on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    context = models.CharField(
        max_length=10,
        choices=CONTEXT_CHOICES,
        blank=True
    )
    vote = models.BooleanField()

    class Meta:
        unique_together = ('user', 'song', 'emotion', 'context')

    def __str__(self):
        return '{} - {} - {}'.format(self.user, self.song, self.emotion)

    def delete(self, *args, **kwargs):
        # We don't actually want to delete these records, so just set the vote value to false
        self.vote = False
        self.save()
