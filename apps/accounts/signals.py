from django.db.models.signals import post_save

from accounts.models import MoodyUser, UserEmotion
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
    sender=MoodyUser,
    dispatch_uid='user_post_save_create_useremotion_records'
)
