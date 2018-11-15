from django import forms

from tunes.models import Emotion


class BrowseSongsForm(forms.Form):
    """Provides validation for /tunes/browse/"""

    emotion = forms.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    jitter = forms.FloatField(min_value=0, max_value=1, required=False)
