from django import forms

from accounts.models import UserSongVote
from tunes.models import Emotion, Song


default_option = [('', '-----------')]


def get_song_genre_choices():
    genres = Song.objects.all().values_list('genre', flat=True).distinct()
    return [(genre, genre) for genre in genres] + default_option


class BrowseForm(forms.Form):
    context_options = UserSongVote.CONTEXT_CHOICES + default_option

    emotion = forms.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    genre = forms.ChoiceField(choices=get_song_genre_choices, required=False)
    context = forms.ChoiceField(choices= context_options, required=False)
    description = forms.CharField(required=False)
