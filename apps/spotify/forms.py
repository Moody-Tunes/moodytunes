from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from accounts.models import UserSongVote
from moodytunes.forms import get_genre_choices
from tunes.models import Emotion, Song


class ExportPlaylistForm(forms.Form):
    emotion = forms.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    playlist_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Playlist Name'}))
    genre = forms.ChoiceField(choices=[], required=False)
    context = forms.ChoiceField(choices=UserSongVote.CONTEXT_CHOICES, required=False)
    cover_image = forms.ImageField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['genre'].choices = get_genre_choices()


class SuggestSongForm(forms.Form):
    code = forms.CharField(
        max_length=36,
        validators=[
            RegexValidator(r'spotify:track:([a-zA-Z0-9]){22}', message='Please enter a valid Spotify code'),
        ]
    )

    def clean_code(self):
        code = self.cleaned_data['code']

        # Ensure song is not already in our system
        if Song.objects.filter(code=code).exists():
            self.add_error(
                'code',
                ValidationError('Song already exists in our system')
            )

        return code
