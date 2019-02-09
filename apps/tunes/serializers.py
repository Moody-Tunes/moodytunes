from rest_framework import serializers

from accounts.models import UserSongVote
from tunes.models import Emotion, Song


class EmotionSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Emotion
        fields = ('name', 'full_name')

    def get_full_name(self, obj):
        return obj.full_name


class SongSerializer(serializers.ModelSerializer):
    class Meta:
        model = Song
        fields = ('artist', 'name', 'genre', 'code')


class VoteSerializer(serializers.ModelSerializer):
    song = SongSerializer()
    emotion = EmotionSerializer()

    class Meta:
        model = UserSongVote
        fields = ('emotion', 'song', 'context', 'description')


class OptionsSerializer(serializers.Serializer):
    emotions = serializers.ListField()
    genres = serializers.ListField()
    context = serializers.ListField()


class BrowseSongsRequestSerializer(serializers.Serializer):
    """Provides validation for /tunes/browse/"""

    emotion = serializers.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    genre = serializers.CharField(max_length=15, required=False)
    jitter = serializers.FloatField(min_value=0, max_value=1, required=False)
    limit = serializers.IntegerField(max_value=25, required=False)


class VoteSongsRequestSerializer(serializers.Serializer):
    """Provides validation for POST /tunes/vote/"""

    emotion = serializers.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    song_code = serializers.CharField()
    vote = serializers.BooleanField()
    context = serializers.ChoiceField(choices=UserSongVote.CONTEXT_CHOICES, required=False)
    description = serializers.CharField(max_length=100, required=False)


class DeleteVoteRequestSerializer(serializers.Serializer):
    """Provides validation for DELETE /tunes/vote/"""

    emotion = serializers.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    song_code = serializers.CharField()


class PlaylistSongsRequestSerializer(serializers.Serializer):
    """Provides validation for /tunes/playlist/"""

    emotion = serializers.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    genre = serializers.CharField(max_length=15, required=False)
    context = serializers.ChoiceField(choices=UserSongVote.CONTEXT_CHOICES, required=False)
