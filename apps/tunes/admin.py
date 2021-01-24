from django import forms
from django.contrib import admin

from base.admin import MoodyBaseAdmin
from moodytunes.forms import get_genre_choices
from tunes.models import Emotion, Song


class GenreFormField(forms.ModelForm):
    genre = forms.ChoiceField(choices=[], required=False)

    class Meta:
        model = Song
        fields = ('genre',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['genre'].choices = get_genre_choices()


class EmotionAdmin(MoodyBaseAdmin):
    list_display = ('full_name', 'energy', 'valence', 'danceability')
    readonly_fields = ('name',)

    def has_add_permission(self, request):
        return False


class SongAdmin(MoodyBaseAdmin):
    list_display = ('code', 'genre', 'artist', 'name', 'valence', 'energy', 'danceability')
    readonly_fields = ('code', 'artist', 'name', 'valence', 'energy', 'danceability')
    list_filter = (('genre', admin.EmptyFieldListFilter), 'genre')
    search_fields = ('code', 'name', 'artist')
    form = GenreFormField

    def has_add_permission(self, request):
        return False


admin.site.register(Emotion, EmotionAdmin)
admin.site.register(Song, SongAdmin)
