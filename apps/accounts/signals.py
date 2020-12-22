from django.conf import settings
from django.contrib.auth.signals import user_login_failed
from django.db.models.signals import post_save

from accounts.models import SpotifyUserAuth, UserSongVote
from accounts.tasks import (
    CreateUserEmotionRecordsForUserTask,
    UpdateTopArtistsFromSpotifyTask,
    UpdateUserEmotionRecordAttributeTask,
)
from accounts.utils import log_failed_login_attempt


def create_user_emotion_records(sender, instance, created, *args, **kwargs):
    # Post save signal to create UserEmotion records for a user on creation
    if created and not instance.is_superuser:
        CreateUserEmotionRecordsForUserTask().delay(instance.pk)


post_save.connect(
    create_user_emotion_records,
    sender=settings.AUTH_USER_MODEL,
    dispatch_uid=settings.CREATE_USER_EMOTION_RECORDS_SIGNAL_UID
)


def update_user_emotion_attributes(sender, instance, created, *args, **kwargs):
    if created and instance.vote:
        UpdateUserEmotionRecordAttributeTask().delay(instance.user_id, instance.emotion_id)
    elif not created:
        UpdateUserEmotionRecordAttributeTask().delay(instance.user_id, instance.emotion_id)


post_save.connect(
    update_user_emotion_attributes,
    sender=UserSongVote,
    dispatch_uid=settings.UPDATE_USER_EMOTION_ATTRIBUTES_SIGNAL_UID
)


def update_spotify_top_artists(sender, instance, created, *args, **kwargs):
    if created:
        UpdateTopArtistsFromSpotifyTask().apply_async((instance.pk,), countdown=30)


post_save.connect(
    update_spotify_top_artists,
    sender=SpotifyUserAuth,
    dispatch_uid=settings.UPDATE_SPOTIFY_DATA_TOP_ARTISTS_SIGNAL_UID
)


user_login_failed.connect(
    log_failed_login_attempt,
    dispatch_uid=settings.LOG_MOODY_USER_FAILED_LOGIN_SIGNAL_UID
)
