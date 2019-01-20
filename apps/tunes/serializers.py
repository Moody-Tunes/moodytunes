from rest_framework import serializers

from tunes.models import Emotion, Song


class SongSerializer(serializers.ModelSerializer):
    class Meta:
        model = Song
        fields = '__all__'


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


class DeleteVoteRequestSerializer(serializers.Serializer):
    """Provides validation for DELETE /tunes/vote/"""

    emotion = serializers.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    song_code = serializers.CharField()


class PlaylistSongsRequestSerializer(serializers.Serializer):
    """Provides validation for /tunes/playlist/"""

    emotion = serializers.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    genre = serializers.CharField(max_length=15, required=False)
