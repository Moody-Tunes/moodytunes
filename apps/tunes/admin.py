from django.contrib import admin

from tunes.models import Emotion, Song


class EmotionAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'lower_bound', 'upper_bound')
    readonly_fields = ('name',)


class SongAdmin(admin.ModelAdmin):
    list_display = ('code', 'artist', 'name', 'valence', 'energy')
    readonly_fields = ('code', 'artist', 'name', 'valence', 'energy')


admin.site.register(Emotion, EmotionAdmin)
admin.site.register(Song, SongAdmin)
