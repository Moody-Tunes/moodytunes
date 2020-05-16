from django import forms
from django.contrib import admin

from base.admin import MoodyBaseAdmin
from moodytunes.forms import get_genre_choices
from tunes.models import Emotion, Song


class NullGenreFilter(admin.SimpleListFilter):
    title = 'Has Genre'
    parameter_name = 'has_genre'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no', 'No')
        )

    def queryset(self, request, queryset):
        if self.value() == 'no':
            return queryset.filter(genre='')
        if self.value() == 'yes':
            return queryset.exclude(genre='')


class GenreFormField(forms.ModelForm):
    genre = forms.ChoiceField(choices=get_genre_choices, required=False)

    class Meta:
        model = Song
        fields = ('genre',)


class EmotionAdmin(MoodyBaseAdmin):
    list_display = ('full_name', 'energy', 'valence', 'danceability')
    readonly_fields = ('name',)

    def has_add_permission(self, request):
        return False


class SongAdmin(MoodyBaseAdmin):
    list_display = ('code', 'genre', 'artist', 'name', 'valence', 'energy', 'danceability')
    readonly_fields = ('code', 'artist', 'name', 'valence', 'energy', 'danceability')
    list_filter = (NullGenreFilter, 'genre')
    form = GenreFormField

    def has_add_permission(self, request):
        return False


admin.site.register(Emotion, EmotionAdmin)
admin.site.register(Song, SongAdmin)
