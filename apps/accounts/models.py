from datetime import timedelta
from logging import getLogger

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from encrypted_model_fields.fields import EncryptedCharField

from base.models import BaseModel
from base.validators import validate_decimal_value
from libs.spotify import SpotifyClient, SpotifyException
from libs.utils import average

logger = getLogger(__name__)


class MoodyUser(BaseModel, AbstractUser):
    """
    Represents a user in our system. Extends Django auth features and includes
    logic needed in course of site flow.
    """

    def get_user_emotion_record(self, emotion_name):
        """
        Return the UserEmotion record for a given Emotion name.

        :param emotion_name: (str) `Emotion.name` constant to retrieve

        :return: (UserEmotion)
        """
        try:
            return self.useremotion_set.get(emotion__name=emotion_name)
        except UserEmotion.DoesNotExist:
            logger.error('User {} has no UserEmotion record for {}'.format(self.username, emotion_name))
            return None

    def update_information(self, data):
        """
        Given a dictionary of CLEAN DATA, update the user information accordingly.
        This method must ONLY be used with clean data and should have keys tied to a Django user model
        like username, email, password, and the like.
        :param data: (dict) Dictionary of data to update for user
        """
        for key, value in data.items():
            if value:
                # Need to be careful about dealing with blank values. If we get an attribute that is blank for this
                # instance (like setting an email for the first time), the value will be "falsey". If we were to do
                # check like `if attr` it would be False and the attribute not updated. We need to do a direct
                # comparison to False in order to be sure that the attribute does NOT exist on the MoodyUser model.
                attr = getattr(self, key, False)
                if attr is not False:
                    setattr(self, key, value)

        self.save()


class SpotifyUserAuth(BaseModel):
    """
    Represent a mapping of a user in our system to a Spotify account.
    Used to authenticate on behalf of a user when connecting with the Spotify API.
    """
    user = models.OneToOneField(MoodyUser, on_delete=models.PROTECT)
    spotify_user_id = models.CharField(max_length=50, unique=True)
    access_token = EncryptedCharField(max_length=100)
    refresh_token = EncryptedCharField(max_length=100)
    last_refreshed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{} - {}'.format(self.user.username, self.spotify_user_id)

    @property
    def should_update_access_token(self):
        """
        Spotify access tokens are good for one hour. If the access token has not been updated in this time period,
        indicate that the access token should be updated
        :return: (bool) True if the access token has been updated since the last hour, False if not
        """
        spotify_auth_timeout = timezone.now() - timedelta(seconds=settings.SPOTIFY['auth_user_token_timeout'])
        return self.last_refreshed < spotify_auth_timeout

    def refresh_access_token(self):
        """Make a call to the Spotify API to refresh the access token for the SpotifyUserAuth records"""
        spotify_client = SpotifyClient(identifier='update-access-token:{}'.format(self.user.username))

        try:
            logger.info(
                'Refreshing access token for {}'.format(self.user.username),
                extra={
                    'fingerprint': 'accounts.SpotifyUserAuth.refresh_access_token',
                    'moodytunes_username': self.user.username,
                    'spotify_username': self.spotify_user_id
                }
            )

            access_token = spotify_client.refresh_access_token(self.refresh_token)

            self.access_token = access_token
            self.last_refreshed = timezone.now()

            self.save()
        except SpotifyException:
            logger.warning('Unable to refresh access token for {}'.format(self.user.username), exc_info=True)

            raise


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

    def update_attributes(self):
        """
        Update the attributes for this user/emotion mapping to the average of the attributes of the songs the user has
        upvoted as making them feel this emotion. If the user doesn't have any upvotes for this emotion, the attributes
        will be set to `None` and reset to the emotion defaults in the save() call
        """
        votes = self.user.usersongvote_set.filter(emotion=self.emotion, vote=True)

        vote_data = average(votes, 'song__valence', 'song__energy', 'song__danceability')
        self.valence = vote_data['song__valence__avg']
        self.energy = vote_data['song__energy__avg']
        self.danceability = vote_data['song__danceability__avg']

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
