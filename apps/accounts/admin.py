from django.contrib import admin

from accounts.forms import UpdateUserEmotionAttributesForm
from accounts.models import MoodyUser, SpotifyUserAuth, UserEmotion, UserSongVote
from base.admin import MoodyBaseAdmin


class MoodyUserAdmin(MoodyBaseAdmin):
    list_display = ('username', 'last_login')
    exclude = ('password',)
    readonly_fields = ('last_login', 'date_joined', 'first_name', 'last_name', 'username',)


class UserEmotionAdmin(MoodyBaseAdmin):
    form = UpdateUserEmotionAttributesForm
    list_display = ('user', 'emotion', 'energy', 'valence', 'danceability', 'vote_count_for_emotion')
    readonly_fields = ('user', 'emotion')
    list_filter = ('emotion',)

    def has_add_permission(self, request):
        return False

    def vote_count_for_emotion(self, obj):
        return obj.user.usersongvote_set.filter(emotion=obj.emotion).count()
    vote_count_for_emotion.short_description = 'Votes'


class UserSongVoteAdmin(MoodyBaseAdmin):
    list_display = ('user', 'song', 'emotion', 'vote', 'context')
    readonly_fields = ('user', 'song', 'emotion', 'vote', 'context', 'description')
    list_filter = ('emotion', 'vote', 'context')
    search_fields = ('user__username',)

    def has_add_permission(self, request):
        return False


class SpotifyUserAuthAdmin(MoodyBaseAdmin):
    list_display = ('user', 'spotify_user_id', 'last_refreshed')
    readonly_fields = ('user', 'spotify_user_id')
    exclude = ('access_token', 'refresh_token')

    def has_add_permission(self, request):
        return False


admin.site.register(MoodyUser, MoodyUserAdmin)
admin.site.register(UserEmotion, UserEmotionAdmin)
admin.site.register(UserSongVote, UserSongVoteAdmin)
admin.site.register(SpotifyUserAuth, SpotifyUserAuthAdmin)
