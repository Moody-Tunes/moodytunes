import re

from rest_framework import serializers

from accounts.models import UserSongVote
from base.fields import CleanedChoiceField
from tunes.models import Emotion, Song


class SongSerializer(serializers.ModelSerializer):
    class Meta:
        model = Song
        fields = ('code',)


class LastPlaylistSerializer(serializers.Serializer):
    emotion = CleanedChoiceField(Emotion.EMOTION_NAME_CHOICES)
    context = CleanedChoiceField(UserSongVote.CONTEXT_CHOICES, required=False)
    description = serializers.CharField(max_length=100, required=False, allow_blank=True)
    playlist = SongSerializer(many=True, read_only=True)


class PlaylistSerializer(serializers.ModelSerializer):
    song = SongSerializer()

    class Meta:
        model = UserSongVote
        fields = ('song', 'context', 'description')


class OptionsSerializer(serializers.Serializer):
    emotions = serializers.ListField()
    genres = serializers.ListField()
    context = serializers.ListField()


class VoteInfoSerializer(serializers.Serializer):
    contexts = serializers.ListField()


class BrowseSongsRequestSerializer(serializers.Serializer):
    """Provides validation for /tunes/browse/"""

    emotion = CleanedChoiceField(
        Emotion.EMOTION_NAME_CHOICES,
        help_text='Emotion to use for generating browse playlist. Must be one of Emotion.EMOTION_NAME_CHOICES'
    )
    artist = serializers.CharField(
        max_length=50,
        required=False,
        help_text='Filter browse playlist for songs by given artist.'
    )
    genre = serializers.CharField(
        max_length=15,
        required=False,
        help_text='Filter browse playlist for songs in given genre.'
    )
    jitter = serializers.FloatField(
        min_value=0,
        max_value=1,
        required=False,
        help_text='Amount to push query values for when looking up songs by their emotion attributes.'
    )
    limit = serializers.IntegerField(
        max_value=25,
        required=False,
        help_text='Number of songs to return in playlist.'
    )
    context = CleanedChoiceField(
        UserSongVote.CONTEXT_CHOICES,
        required=False,
        help_text='Context for user listening session.'
    )
    description = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text='Description for user listening session.'
    )


class VoteSongsRequestSerializer(serializers.Serializer):
    """Provides validation for POST /tunes/vote/"""

    emotion = CleanedChoiceField(Emotion.EMOTION_NAME_CHOICES)
    song_code = serializers.CharField()
    vote = serializers.BooleanField()
    context = CleanedChoiceField(UserSongVote.CONTEXT_CHOICES, required=False)
    description = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate_description(self, value):
        if value and not re.match(r"^[a-zA-Z0-9_.?!, ]*$", value):
            raise serializers.ValidationError('Value must only contain alphanumeric characters')

        return value


class DeleteVoteRequestSerializer(serializers.Serializer):
    """Provides validation for DELETE /tunes/vote/"""

    emotion = CleanedChoiceField(Emotion.EMOTION_NAME_CHOICES)
    song_code = serializers.CharField()
    context = CleanedChoiceField(UserSongVote.CONTEXT_CHOICES, required=False)


class PlaylistSongsRequestSerializer(serializers.Serializer):
    """Provides validation for /tunes/playlist/"""

    emotion = CleanedChoiceField(
        Emotion.EMOTION_NAME_CHOICES,
        help_text='Emotion of playlist to view. Must be one of Emotion.EMOTION_NAME_CHOICES'
    )
    genre = serializers.CharField(
        max_length=15,
        required=False,
        help_text='Filter emotion playlist for songs in given genre.'
    )
    context = CleanedChoiceField(
        UserSongVote.CONTEXT_CHOICES,
        required=False,
        help_text='Return songs for the emotion the user has upvoted for a given context.'
    )
    artist = serializers.CharField(
        max_length=50,
        required=False,
        help_text='Filter emotion playlist for songs by given artist.'
    )


class VoteInfoRequestSerializer(serializers.Serializer):
    """Provides validation for /tunes/vote/info/"""

    emotion = CleanedChoiceField(Emotion.EMOTION_NAME_CHOICES)
    song_code = serializers.CharField()
