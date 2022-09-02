import random

from django import forms
from django.conf import settings
from django.core.cache import cache

from accounts.models import UserSongVote
from base.forms import RangeInput
from tunes.models import Emotion, Song


default_option = [('', '-----------')]


def get_genre_choices():
    """
    Return genre choices for form field.

    :return: (list[tuples]) List of options for genre field in forms
    """
    genres = cache.get(settings.GENRE_CHOICES_CACHE_KEY)

    if not genres:
        genres = list(Song.objects.all().values_list('genre', flat=True).distinct().order_by('genre'))
        cache.set(settings.GENRE_CHOICES_CACHE_KEY, genres, settings.GENRE_CHOICES_CACHE_TIMEOUT)

    return default_option + [(genre, genre.split('_')[0].capitalize()) for genre in genres if genre]


class BrowseForm(forms.Form):
    emotion = forms.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    artist = forms.CharField(max_length=50, required=False)
    genre = forms.ChoiceField(choices=[], required=False)
    context = forms.ChoiceField(
        choices=UserSongVote.CONTEXT_CHOICES,
        required=False,
        widget=forms.widgets.Select(attrs={'class': 'select-context-input'})
    )
    description = forms.CharField(required=False)
    jitter = forms.FloatField(
        required=False,
        min_value=0,
        max_value=0.5,
        widget=RangeInput(attrs={'step': .05, 'class': 'slider', 'value': settings.BROWSE_DEFAULT_JITTER})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['genre'].choices = get_genre_choices()

        if not self.initial.get('emotion'):
            self.fields['emotion'].initial = random.choice(self.fields['emotion'].choices)


class PlaylistForm(forms.Form):
    emotion = forms.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    genre = forms.ChoiceField(choices=[], required=False)
    context = forms.ChoiceField(choices=UserSongVote.CONTEXT_CHOICES, required=False)
    artist = forms.CharField(max_length=50, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['genre'].choices = get_genre_choices()
