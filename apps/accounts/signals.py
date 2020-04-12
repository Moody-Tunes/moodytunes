from django.conf import settings
from django.db.models.signals import post_save

from accounts.models import UserSongVote
from accounts.tasks import create_user_emotion_records_for_user, update_user_emotion_record_attributes


def create_user_emotion_records(sender, instance, created, *args, **kwargs):
    # Post save signal to create UserEmotion records for a user on creation
    if created:
        create_user_emotion_records_for_user.delay(instance.pk)


post_save.connect(
    create_user_emotion_records,
    sender=settings.AUTH_USER_MODEL,
    dispatch_uid='user_post_save_create_useremotion_records'
)


def update_user_emotion_attributes(sender, instance, created, *args, **kwargs):
    if instance.vote and created:
        update_user_emotion_record_attributes.delay(instance.pk)


post_save.connect(
    update_user_emotion_attributes,
    sender=UserSongVote,
    dispatch_uid='user_song_vote_post_save_update_useremotion_attributes'
)
