from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

from base.models import BaseModel
from base.validators import validate_decimal_value


class UserPrefetchManager(UserManager):
    """Manager to automatically `prefetch_related` records when querying the MoodyUser model"""
    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            'useremotion_set__emotion',
            'usersongvote_set__emotion',
            'usersongvote_set__song',
        )


class MoodyUser(BaseModel, AbstractUser):
    """
    Represents a user in our system. Extends Django auth features and includes
    logic needed in course of site flow.
    """
    prefetch_manager = UserPrefetchManager()

    def get_user_emotion_record(self, emotion_name):
        """
        Return the UserEmotion record for a given name. This is done in Python to take advantage of `prefetch_related`
        caching. Note that you would need to prefetch the `useremotion_set` related manager; this will happen for you
        if you make your query using the `MoodyUser.prefetch_manager` manager.

        :param emotion_name: (str) `Emotion.name` constant to retrieve
        :> return:
            - `UserEmotion` record for the given `emotion_name`
            - `None` if `emotion_name` is not valid
        """
        for user_emotion in self.useremotion_set.all():
            if user_emotion.emotion.name == emotion_name:
                return user_emotion

        return None

    def get_user_song_vote_records(self, emotion_name):
        """
        Return the list of UserSongVote records for a given emotion. This is done in Python to take advantage of
        `prefetch_related` caching. Note that you would need to prefetch the `useresongvote_set` related manager;
        this will happen for you if you make your query using the `MoodyUser.prefetch_manager` manager.

        :param emotion_name: (str) `Emotion.name` constant to retrieve

        :return: (list) Collection of votes for the given emotion
        """
        return [vote for vote in self.usersongvote_set.all() if vote.emotion.name == emotion_name]

    def update_information(self, data):
        """
        Given a dictionary of CLEAN DATA, update the user information accordingly.
        This method must ONLY be used with clean data and should have keys tied to a Django user model
        like username, email, password, and the like.
        :param data: (dict) Dictionary of data to update for user
        """
        for key, value in data.items():
            if value:
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
    energy = models.FloatField(validators=[validate_decimal_value])
    valence = models.FloatField(validators=[validate_decimal_value])

    class Meta:
        unique_together = ('user', 'emotion')

    def __str__(self):
        return '{} - {}'.format(self.user, self.emotion)

    def save(self, *args, **kwargs):
        # Set energy and valence to emotion defaults
        if not self.energy:
            self.energy = self.emotion.energy

        if not self.valence:
            self.valence = self.emotion.valence

        super().save(*args, **kwargs)

    def update_emotion_boundaries(self, valence, energy, reset=False):
        """
        Given the valence and energy of a song, recompute boundaries for the given emotion box
        :param valence: (float) Representation of song mood
        :param energy: (float) Representation of song intensity
        :param change: (bool) Flag to denote resetting the boundaries for a record. Used in the case a user "unvotes"
        a song to reset the boundaries for that emotion
        """
        if reset:
            self.valence = 2 * self.valence - valence
            self.energy = 2 * self.energy - energy
        else:
            self.valence = (self.valence + valence) / 2
            self.energy = (self.energy + energy) / 2
        self.save()


class UserSongVote(BaseModel):
    """
    Represents a mapping between a user and a song denoting whether or not the
    song made the user feel the linked emotion. This table will be used to
    track what songs a user associates with a particular emotion.
    """
    CONTEXT_CHOICES = [
        ('PARTY', 'Listening to music at a party'),
        ('RELAX', 'Listening to music to relax'),
        ('WORK', 'Listening to music while working on a task'),
        ('OTHER', 'Doing something else')
    ]

    user = models.ForeignKey(MoodyUser, on_delete=models.CASCADE)
    song = models.ForeignKey('tunes.Song', on_delete=models.CASCADE)
    emotion = models.ForeignKey('tunes.Emotion', on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    context = models.CharField(
        max_length=10,
        choices=CONTEXT_CHOICES,
        blank=True
    )
    vote = models.BooleanField()

    def __str__(self):
        return '{} - {} - {}'.format(self.user, self.song, self.emotion)

    def delete(self, *args, **kwargs):
        # Update the user_emotion boundaries for the given emotion
        user_emot = self.user.useremotion_set.get(emotion=self.emotion)
        user_emot.update_emotion_boundaries(
            self.song.valence,
            self.song.energy,
            reset=True
        )

        # We don't actually want to delete these records, so just set the vote value to false
        self.vote = False
        self.save()
