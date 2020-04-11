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


def update_user_emotion_attributes(sender, instance, created, *args, **kwargs):
    if instance.vote and created:
        # We should always call get_or_create to ensure that if we add new emotions, we'll auto
        # create the corresponding UserEmotion record the first time a user votes on a song
        # for the emotion

        user_emotion, _ = instance.user.useremotion_set.get_or_create(
            emotion__name=instance.emotion.name,
            defaults={
                'user': instance.user,
                'emotion': instance.emotion
            }
        )

        user_emotion.update_attributes()


post_save.connect(
    update_user_emotion_attributes,
    sender=UserSongVote,
    dispatch_uid='user_song_vote_post_save_update_useremotion_attributes'
)
