from django.contrib.auth.models import AbstractUser
from django.db import models

from base.models import BaseModel


class MoodyUser(BaseModel, AbstractUser):
    pass


class UserEmotion(BaseModel):
    user = models.ManyToManyField(MoodyUser)
    emotion = models.ManyToManyField('tunes.Emotion')
    lower_bound = models.FloatField()
    upper_bound = models.FloatField()

    def save(self, *args, **kwargs):
        # TODO: Set `lower_bound` and `upper_bound` to `emotion` defaults
        pass

    def update_emotion_boundaries(self, emotion_name, song_name):
        # TODO: Figure out what to do about updating the boundaries given a
        # song the user votes makes them feel a given emotion
        pass


class UserSongVote(BaseModel):
    user = models.ManyToManyField(MoodyUser)
    song = models.ManyToManyField('tunes.Song')
    emotion = models.ManyToManyField('tunes.Emotion')
    vote = models.BooleanField()

    def save(self, *args, **kwargs):
        # TODO: Update UserEmotion record if song was upvoted
        pass
