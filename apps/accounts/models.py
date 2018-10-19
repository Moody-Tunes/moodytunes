from django.contrib.auth.models import AbstractUser
from django.db import models

from base.models import BaseModel


class MoodyUser(BaseModel, AbstractUser):
    """
    Represents a user in our system. Extends Django auth features and includes
    logic needed in course of site flow.
    """
    def update_information(self, data):
        """
        Given a dictionary of CLEAN DATA, update the user information accordingly.
        This method must ONLY be used with clean data and should have keys tied to a Django user model
        like username, email, password, and the like.
        :@ param data: (dict) Dictionary of data to update for user
        """
        for key, value in data.items():
            if value:
                if key == 'password':
                    # Need to use helper method to set user password
                    self.set_password(value)
                elif getattr(self, key, False):
                    setattr(self, key, value)

        self.save()


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

    class Meta:
        unique_together = ('user', 'emotion')

    def __str__(self):
        return '{} - {}'.format(self.user, self.emotion)

    def save(self, *args, **kwargs):
        # Set lower_bound and upper_bound to emotion defaults
        if not self.lower_bound:
            self.lower_bound = self.emotion.lower_bound

        if not self.upper_bound:
            self.upper_bound = self.emotion.upper_bound

        super().save(*args, **kwargs)

    def update_emotion_boundaries(self, valence, energy):
        """
        Given a valence and energy, recompute boundaries for the given emotion
        box. `valence` governs the upper_bound values while energy determines
        the lower_bound values.
        """
        self.upper_bound = (self.upper_bound + valence) / 2
        self.lower_bound = (self.lower_bound + energy) / 2
        self.save()


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

    def __str__(self):
        return '{} - {} - {}'.format(self.user, self.song, self.emotion)
