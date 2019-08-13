from django.contrib import admin

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


class EmotionAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'energy', 'valence')
    readonly_fields = ('name',)


class SongAdmin(admin.ModelAdmin):
    list_display = ('code', 'genre', 'artist', 'name', 'valence', 'energy')
    readonly_fields = ('code', 'artist', 'name', 'valence', 'energy')
    list_filter = (NullGenreFilter, 'genre')


admin.site.register(Emotion, EmotionAdmin)
admin.site.register(Song, SongAdmin)
