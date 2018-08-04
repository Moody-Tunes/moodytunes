from django.contrib.auth.models import AbstractUser
from django.db import models

from base.models import BaseModel


class MoodyUser(BaseModel, AbstractUser):
    """
    Represents a user in our system. Extends Django auth features and includes
    logic needed in course of site flow.
    """
    pass


class UserEmotion(BaseModel):
    """
    Represents a mapping between a particular user and an emotion. This allows
    us to store separate boundaries for each user for each emotion. Unless
    values are specified upon creation, the boundaries will be set to the
    defaults defined in the `Emotion` table.
    """
    user = models.ForeignKey(MoodyUser, on_delete=models.CASCADE)
    emotion = models.ForeignKey('tunes.Emotion', on_delete=models.CASCADE)
    lower_bound = models.FloatField()
    upper_bound = models.FloatField()

    def save(self, *args, **kwargs):
        # Set lower_bound and upper_bound to emotion defaults
        if not self.lower_bound:
            self.lower_bound = self.emotion.lower_bound

        if not self.upper_bound:
            self.upper_bound = self.emotion.upper_bound

        super().save(*args, **kwargs)

    def update_emotion_boundaries(self, emotion_name, song_name):
        # TODO: Figure out what to do about updating the boundaries given a
        # song the user votes makes them feel a given emotion
        pass


class UserSongVote(BaseModel):
    """
    Represents a mapping between a user and a song denoting whether or not the
    song made the user feel the linked emotion. This table will be used to
    track what songs a user associates with a particular emotion.
    """
    user = models.ForeignKey(MoodyUser, on_delete=models.CASCADE)
    song = models.ForeignKey('tunes.Song', on_delete=models.CASCADE)
    emotion = models.ForeignKey('tunes.Emotion', on_delete=models.CASCADE)
    vote = models.BooleanField()

    def save(self, *args, **kwargs):
        # TODO: Update UserEmotion record if song was upvoted
        pass
