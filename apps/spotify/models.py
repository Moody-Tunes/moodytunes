import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from fernet_fields import EncryptedCharField
from spotify_client import SpotifyClient
from spotify_client.exceptions import SpotifyException

from base.models import BaseModel
from libs.moody_logging import auto_fingerprint, update_logging_data


logger = logging.getLogger(__name__)


class SpotifyUserData(BaseModel):
    """
    Stores data from Spotify listening habits for a user
    that we can use to offer a more personalized MoodyTunes experience.
    """
    top_artists = ArrayField(models.CharField(max_length=200), default=list)
    spotify_auth = models.OneToOneField('spotify.SpotifyAuth', on_delete=models.CASCADE)


class SpotifyAuth(BaseModel):
    """
    Represent a mapping of a user in our system to a Spotify account.
    Used to authenticate on behalf of a user when connecting with the Spotify API.
    """
    user = models.OneToOneField('accounts.MoodyUser', on_delete=models.CASCADE)
    spotify_user_id = models.CharField(max_length=50, unique=True)
    access_token = EncryptedCharField(max_length=100)
    refresh_token = EncryptedCharField(max_length=100)
    last_refreshed = models.DateTimeField(auto_now_add=True)
    scopes = ArrayField(models.CharField(max_length=30), default=list)

    def __str__(self):
        return '{} - {}'.format(self.user.username, self.spotify_user_id)

    @classmethod
    @update_logging_data
    def get_and_refresh_spotify_auth_record(cls, auth_id, **kwargs):
        """
        Fetch the SpotifyUserAuth record for the given primary key, and refresh if
        the access token is expired

        :param auth_id: (int) Primary key for SpotifyUserAuth record

        :return: (SpotifyUserAuth)
        """
        try:
            auth = cls.objects.get(pk=auth_id)
        except (SpotifyAuth.MultipleObjectsReturned, SpotifyAuth.DoesNotExist):
            logger.error(
                'Failed to fetch SpotifyUserAuth with pk={}'.format(auth_id),
                extra={'fingerprint': auto_fingerprint('failed_to_fetch_spotify_user_auth', **kwargs)},
            )

            raise

        if auth.should_refresh_access_token:
            auth.refresh_access_token()

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
        spotify_client = SpotifyClient(identifier='refresh-access-token:{}'.format(self.spotify_user_id))

        try:
            access_token = spotify_client.refresh_access_token(self.refresh_token)

            self.access_token = access_token
            self.last_refreshed = timezone.now()

            self.save()

            logger.info(
                'Refreshed access token for {}'.format(self.spotify_user_id),
                extra={
                    'fingerprint': auto_fingerprint('success_refresh_access_token', **kwargs),
                    'spotify_username': self.spotify_user_id,
                    'auth_id': self.pk
                }
            )

        except SpotifyException:
            logger.exception(
                'Unable to refresh access token for {}'.format(self.spotify_user_id),
                extra={
                    'fingerprint': auto_fingerprint('failed_refresh_access_token', **kwargs),
                    'spotify_username': self.spotify_user_id,
                    'auth_id': self.pk,
                    'user_id': self.user_id
                }
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
