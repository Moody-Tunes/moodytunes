from datetime import timedelta
from logging import getLogger

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from encrypted_model_fields.fields import EncryptedCharField
from spotify_client import SpotifyClient
from spotify_client.exceptions import SpotifyException

from base.models import BaseModel
from base.validators import validate_decimal_value
from libs.moody_logging import auto_fingerprint, update_logging_data
from libs.utils import average


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


class SpotifyUserData(BaseModel):
    """
    Stores data from Spotify listening habits for a user
    that we can use to offer a more personalized MoodyTunes experience.
    """
    top_artists = ArrayField(models.CharField(max_length=200), default=list)


class SpotifyUserAuth(BaseModel):
    """
    Represent a mapping of a user in our system to a Spotify account.
    Used to authenticate on behalf of a user when connecting with the Spotify API.
    """
    user = models.OneToOneField(MoodyUser, on_delete=models.CASCADE)
    spotify_user_id = models.CharField(max_length=50, unique=True)
    access_token = EncryptedCharField(max_length=100)
    refresh_token = EncryptedCharField(max_length=100)
    last_refreshed = models.DateTimeField(auto_now_add=True)
    scopes = ArrayField(models.CharField(max_length=30), default=list)
    spotify_data = models.OneToOneField(SpotifyUserData, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return '{} - {}'.format(self.user.username, self.spotify_user_id)

    def save(self, *args, **kwargs):
        if self.spotify_data is None:
            self.spotify_data = SpotifyUserData.objects.create(spotifyuserauth=self)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete related SpotifyUserData record if it exists
        if self.spotify_data is not None:
            self.spotify_data.delete()

        super().delete(*args, **kwargs)

    @classmethod
    @update_logging_data
    def get_and_refresh_spotify_user_auth_record(cls, auth_id, **kwargs):
        """
        Fetch the SpotifyUserAuth record for the given primary key, and refresh if
        the access token is expired

        :param auth_id: (int) Primary key for SpotifyUserAuth record

        :return: (SpotifyUserAuth)
        """
        try:
            auth = SpotifyUserAuth.objects.get(pk=auth_id)
        except (SpotifyUserAuth.MultipleObjectsReturned, SpotifyUserAuth.DoesNotExist):
            logger.error(
                'Failed to fetch SpotifyUserAuth with pk={}'.format(auth_id),
                extra={'fingerprint': auto_fingerprint('failed_to_fetch_spotify_user_auth', **kwargs)},
            )

            raise

        if auth.should_refresh_access_token:
            try:
                auth.refresh_access_token()
            except SpotifyException:
                logger.warning(
                    'Failed to update access token for SpotifyUserAuth with pk={}'.format(auth_id),
                    extra={'fingerprint': auto_fingerprint('failed_to_update_access_token', **kwargs)},
                )
                raise

        return auth

    @property
    def should_refresh_access_token(self):
        """
        Determine if the access token for the record is still valid. Spotify considers access tokens
        that are older than one hour expired and are not accepted for API requests.

        :return: (bool)
        """
        spotify_auth_timeout = timezone.now() - timedelta(seconds=settings.SPOTIFY['auth_user_token_timeout'])
        return self.last_refreshed < spotify_auth_timeout

    @update_logging_data
    def refresh_access_token(self, **kwargs):
        """Make a call to the Spotify API to refresh the access token for the SpotifyUserAuth record"""
        spotify_client = SpotifyClient(identifier='refresh-access-token:{}'.format(self.user.username))

        try:
            access_token = spotify_client.refresh_access_token(self.refresh_token)

            self.access_token = access_token
            self.last_refreshed = timezone.now()

            self.save()

            logger.info(
                'Refreshed access token for {}'.format(self.user.username),
                extra={
                    'fingerprint': auto_fingerprint('success_refresh_access_token', **kwargs),
                    'moodytunes_username': self.user.username,
                    'spotify_username': self.spotify_user_id
                }
            )

        except SpotifyException:
            logger.warning(
                'Unable to refresh access token for {}'.format(self.user.username),
                extra={'fingerprint': auto_fingerprint('failed_refresh_access_token', **kwargs)},
                exc_info=True
            )

            raise

    def has_scope(self, scope):
        """
        Check if the record has the specified Spotify OAuth scope in its collection of authorized
        scopes from Spotify.

        :param scope: (str) Desired Spotify OAuth scope

        :return: (bool)
        """
        return scope in self.scopes


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
        # Get distinct votes by song, to avoid factoring multiple votes for a song into the emotion average
        vote_ids = self.user.usersongvote_set.filter(
            emotion=self.emotion,
            vote=True
        ).distinct(
            'song__code'
        ).values_list(
            'id',
            flat=True
        )

        votes = UserSongVote.objects.filter(id__in=vote_ids)

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
