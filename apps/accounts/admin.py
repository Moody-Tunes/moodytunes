from django.contrib import admin

from accounts.forms import UpdateUserEmotionBoundariesForm
from accounts.models import MoodyUser, UserEmotion, UserSongVote


class MoodyUserAdmin(admin.ModelAdmin):
    list_display = ('username',)
    exclude = ('password',)
    readonly_fields = (
        'last_login', 'date_joined', 'first_name', 'last_name', 'username',
    )


class UserEmotionAdmin(admin.ModelAdmin):
    form = UpdateUserEmotionBoundariesForm
    list_display = ('user', 'emotion', 'lower_bound', 'upper_bound')
    readonly_fields = ('user', 'emotion')
    list_filter = ('emotion',)

    def has_add_permission(self, request):
        return False


class UserSongVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'song', 'emotion', 'vote')
    readonly_fields = ('user', 'song', 'emotion', 'vote')
    list_filter = ('emotion', 'vote')

    def has_add_permission(self, request):
        return False


admin.site.register(MoodyUser, MoodyUserAdmin)
admin.site.register(UserEmotion, UserEmotionAdmin)
admin.site.register(UserSongVote, UserSongVoteAdmin)
