import random

from django import forms

from accounts.models import UserSongVote
from base.forms import RangeInput
from tunes.models import Emotion, Song


default_option = [('', '-----------')]


def get_song_genre_choices(user=None):
    """
    Return genre options for form field. If user is supplied, only return genres from user upvoted songs
    :param user: (MoodyUser) If present, will only return genres from songs user has upvoted
    :return: (list[tuples]) List of options for genre field in forms
    """
    if user:
        genres = UserSongVote.objects.filter(
            user=user,
            vote=True
        ).values_list('song__genre', flat=True).distinct()
    else:
        genres = Song.objects.all().values_list('genre', flat=True).distinct()
    return default_option + [(genre, genre) for genre in genres]


class BrowseForm(forms.Form):
    emotion = forms.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    genre = forms.ChoiceField(choices=get_song_genre_choices, required=False)
    context = forms.ChoiceField(choices=UserSongVote.CONTEXT_CHOICES, required=False)
    description = forms.CharField(required=False)
    jitter = forms.FloatField(
        required=False,
        min_value=0,
        max_value=0.5,
        widget=RangeInput(attrs={'step': .05, 'class': 'slider', 'value': .15})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set the initial emotion to a random value to avoid the "default" option being overly selected
        self.fields['emotion'].initial = random.choice(self.fields['emotion'].choices)


class PlaylistForm(forms.Form):
    emotion = forms.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    genre = forms.ChoiceField(choices=(), required=False)
    context = forms.ChoiceField(choices=UserSongVote.CONTEXT_CHOICES, required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(PlaylistForm, self).__init__(*args, **kwargs)

        # Limit genre choices to those of songs the user has previously upvoted
        self.fields['genre'].choices = get_song_genre_choices(user=user)
