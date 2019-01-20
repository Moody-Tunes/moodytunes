from django import forms

from tunes.models import Emotion
from tunes.utils import get_available_genres


class BrowseSongsForm(forms.Form):
    """Provides validation for /tunes/browse/"""

    emotion = forms.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    genre = forms.ChoiceField(choices=get_available_genres, required=False)
    jitter = forms.FloatField(min_value=0, max_value=1, required=False)
    limit = forms.IntegerField(max_value=25, required=False)


class VoteSongsForm(forms.Form):
    """Provides validation for POST /tunes/vote/"""

    emotion = forms.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    song_code = forms.CharField()
    vote = forms.BooleanField()


class DeleteVoteForm(forms.Form):
    """Provides validation for DELETE /tunes/vote/"""

    emotion = forms.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    song_code = forms.CharField()


class PlaylistSongsForm(forms.Form):
    """Provides validation for /tunes/playlist/"""

    emotion = forms.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    genre = forms.ChoiceField(choices=get_available_genres, required=False)
