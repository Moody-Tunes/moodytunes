from django.contrib import admin
from django.db.models import Q, Count

from accounts.forms import UpdateUserEmotionAttributesForm
from accounts.models import MoodyUser, SpotifyUserAuth, UserEmotion, UserSongVote
from base.admin import MoodyBaseAdmin
from tunes.models import Emotion


emotion_vote_count_map = {
    'MEL': 'melancholy_vote_count',
    'CLM': 'calm_vote_count',
    'HPY': 'happy_vote_count',
    'EXC': 'excited_vote_count'
}


class MoodyUserAdmin(MoodyBaseAdmin):
    list_display = ('username', 'last_login')
    exclude = ('password',)
    readonly_fields = ('last_login', 'date_joined', 'first_name', 'last_name', 'username',)


class UserEmotionAdmin(MoodyBaseAdmin):
    form = UpdateUserEmotionAttributesForm
    list_display = ('user', 'emotion', 'energy', 'valence', 'danceability', 'votes_for_emotion')
    readonly_fields = ('user', 'emotion')
    list_filter = ('emotion',)
    search_fields = ('user__username',)

    def get_queryset(self, request):
        queryset = super(UserEmotionAdmin, self).get_queryset(request).select_related('user', 'emotion')

        # Annotate queryset with count of votes for emotion for each user
        queryset = queryset.annotate(
            melancholy_vote_count=Count(
                'user__usersongvote',
                filter=Q(user__usersongvote__emotion__name=Emotion.MELANCHOLY, user__usersongvote__vote=True)
            ),
            calm_vote_count=Count(
                'user__usersongvote',
                filter=Q(user__usersongvote__emotion__name=Emotion.CALM, user__usersongvote__vote=True)
            ),
            happy_vote_count=Count(
                'user__usersongvote',
                filter=Q(user__usersongvote__emotion__name=Emotion.HAPPY, user__usersongvote__vote=True)
            ),
            excited_vote_count=Count(
                'user__usersongvote',
                filter=Q(user__usersongvote__emotion__name=Emotion.EXCITED, user__usersongvote__vote=True)
            ),
        )

        return queryset

    def has_add_permission(self, request):
        return False

    def votes_for_emotion(self, obj):
        field_name = emotion_vote_count_map[obj.emotion.name]
        return getattr(obj, field_name)
    votes_for_emotion.short_description = 'Votes'


class UserSongVoteAdmin(MoodyBaseAdmin):
    list_display = ('user', 'song', 'emotion', 'vote', 'context')
    readonly_fields = ('user', 'song', 'emotion', 'vote', 'context', 'description')
    list_filter = ('emotion', 'vote', 'context')
    search_fields = ('user__username',)

    def has_add_permission(self, request):
        import pdb
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
