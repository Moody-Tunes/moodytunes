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


class BrowseSongsRequestSerializer(serializers.Serializer):
    """Provides validation for /tunes/browse/"""

    emotion = CleanedChoiceField(Emotion.EMOTION_NAME_CHOICES)
    artist = serializers.CharField(max_length=50, required=False)
    genre = serializers.CharField(max_length=15, required=False)
    jitter = serializers.FloatField(min_value=0, max_value=1, required=False)
    limit = serializers.IntegerField(max_value=25, required=False)
    context = CleanedChoiceField(UserSongVote.CONTEXT_CHOICES, required=False)
    description = serializers.CharField(max_length=100, required=False, allow_blank=True)


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

    emotion = CleanedChoiceField(Emotion.EMOTION_NAME_CHOICES)
    genre = serializers.CharField(max_length=15, required=False)
    context = CleanedChoiceField(UserSongVote.CONTEXT_CHOICES, required=False)
    artist = serializers.CharField(max_length=50, required=False)
