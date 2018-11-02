from django.contrib.auth.models import AbstractUser
from django.db import models

from base.models import BaseModel


class UserEmotionPrefetchManager(models.Manager):
    """Manager to automatically add `prefetch_related` to the useremotion_set for a given user"""
    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            'useremotion_set__emotion',
        )


class MoodyUser(BaseModel, AbstractUser):
    """
    Represents a user in our system. Extends Django auth features and includes
    logic needed in course of site flow.
    """
    cached_emotions = UserEmotionPrefetchManager()

    def get_user_emotion_record(self, emotion_name):
        """
        Return the UserEmotion record for a given name. This is done in Python to take advantage of `prefetch_related`
        caching. Note that you would need to prefetch the `useremotion_set` related manager; this will happen for you
        if you call the `MoodyUser.cached_emotions` manager.

        :@ param emotion_name: (str) `Emotion.name` constant to retrive
        :> return:
            - `UserEmotion` record for the given `emotion_name`
            - `None` if `emotion_name` is not valid
        """
        for user_emotion in self.useremotion_set.all():
            if user_emotion.emotion.name == emotion_name:
                return user_emotion

        return None

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
                else:
                    # Need to be careful about dealing with blank values. If we get an attribute that is blank for this
                    # instance (like setting an email for the first time), the value will be "falsey". If we were to do
                    # check like `if attr` it would be False and the attribute not updated. We need to do a direct
                    # comparison to False in order to be sure that the attribute does NOT exist on the MoodyUser model.
                    attr = getattr(self, key, False)
                    if attr is not False:
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
