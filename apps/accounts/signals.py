from django.conf import settings
from django.db.models.signals import post_save

from accounts.models import UserEmotion, UserSongVote
from tunes.models import Emotion


def create_user_emotion_records(sender, instance, created, *args, **kwargs):
    # Post save signal to create UserEmotion records for a user on creation
    if created:
        for emotion in Emotion.objects.all().iterator():
            UserEmotion.objects.create(
                user=instance,
                emotion=emotion
            )


post_save.connect(
    create_user_emotion_records,
    sender=settings.AUTH_USER_MODEL,
    dispatch_uid='user_post_save_create_useremotion_records'
)


def update_user_attributes(sender, instance, created, *args, **kwargs):
    # Get the boundary record for the given user and emotion
    # We should always call this to ensure that if we add new emotions, we'll auto
    # create the corresponding record when a user starts to browse for songs in
    # that emotion
    user_emot, _ = instance.user.useremotion_set.get_or_create(
        emotion__name=instance.emotion.name,
        defaults={
            'user': instance.user,
            'emotion': instance.emotion
        }
    )

    if instance.vote and created:
        user_emot.update_attributes()


post_save.connect(
    update_user_attributes,
    sender=UserSongVote,
    dispatch_uid='user_song_vote_post_save_update_useremotion_attributes'
)
