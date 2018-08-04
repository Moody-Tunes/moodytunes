from django.db.models.signals import post_save

from accounts.models import MoodyUser, UserEmotion, UserSongVote
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

def update_user_boundaries(sender, instance, created, *args, **kwargs):
    # If vote is positive (song makes user feel emotion) update the
    # boundaries for the given user_emotion with the song attributes
    if instance.vote and created:
        user_emot, _ = instance.user.useremotion_set.get_or_create(
            emotion__name=instance.emotion.name,
            defaults={
                'user': instance.user,
                'emotion': instance.emotion
            }
        )

        user_emot.update_emotion_boundaries(
            instance.song.valence,
            instance.song.energy
        )

post_save.connect(
    update_user_boundaries,
    sender=UserSongVote,
    dispatch_uid='user_song_vote_post_save_update_useremotion_boundaries'
)
