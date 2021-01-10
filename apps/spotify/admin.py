from django.contrib import admin

from base.admin import MoodyBaseAdmin
from spotify.models import SpotifyAuth


class SpotifyUserAuthAdmin(MoodyBaseAdmin):
    list_display = ('user', 'spotify_user_id', 'last_refreshed', 'scopes')
    readonly_fields = ('user', 'spotify_user_id', 'scopes')
    exclude = ('access_token', 'refresh_token', 'spotify_data')

    def has_add_permission(self, request):
        return False


admin.site.register(SpotifyAuth, SpotifyUserAuthAdmin)
