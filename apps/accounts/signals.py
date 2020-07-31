from django.conf import settings
from django.db.models.signals import post_save

from accounts.models import SpotifyUserAuth, UserSongVote
from accounts.tasks import (
    CreateUserEmotionRecordsForUserTask,
    UpdateTopArtistsFromSpotifyTask,
    UpdateUserEmotionRecordAttributeTask,
)


def create_user_emotion_records(sender, instance, created, *args, **kwargs):
    # Post save signal to create UserEmotion records for a user on creation
    if created and not instance.is_superuser:
        CreateUserEmotionRecordsForUserTask().delay(instance.pk)


post_save.connect(
    create_user_emotion_records,
    sender=settings.AUTH_USER_MODEL,
    dispatch_uid='user_post_save_create_useremotion_records'
)


def update_user_emotion_attributes(sender, instance, created, *args, **kwargs):
    if created and instance.vote:
        UpdateUserEmotionRecordAttributeTask().delay(instance.pk)
    elif not created:
        UpdateUserEmotionRecordAttributeTask().delay(instance.pk)


post_save.connect(
    update_user_emotion_attributes,
    sender=UserSongVote,
    dispatch_uid='user_song_vote_post_save_update_useremotion_attributes'
)


def update_spotify_top_artists(sender, instance, created, *args, **kwargs):
    if created:
        UpdateTopArtistsFromSpotifyTask().apply_async((instance.pk,), countdown=30)


post_save.connect(
    update_spotify_top_artists,
    sender=SpotifyUserAuth,
    dispatch_uid='spotify_user_auth_post_save_update_top_artist'
)
