from django import forms

from tunes.models import Emotion, Song


def get_available_genres():
    """
    Return the different genres we have in our system.
    Need to return a two-tuple per Django form standards
    """
    genres = Song.objects.all().values_list('genre', flat=True).distinct()
    return [(genre, genre) for genre in genres]


class BrowseSongsForm(forms.Form):
    """Provides validation for /tunes/browse/"""

    emotion = forms.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    genre = forms.ChoiceField(choices=get_available_genres, required=False)
    jitter = forms.FloatField(min_value=0, max_value=1, required=False)
    limit = forms.IntegerField(max_value=25, required=False)


class VoteSongsForm(forms.Form):
    """Provides validation for /tunes/vote/"""

    emotion = forms.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    song_code = forms.CharField()
    vote = forms.BooleanField()


class PlaylistSongsForm(forms.Form):
    """Provides validation for /tunes/playlist/"""

    emotion = forms.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    genre = forms.ChoiceField(choices=get_available_genres, required=False)
