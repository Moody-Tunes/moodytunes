from rest_framework import serializers

from accounts.models import UserSongVote
from tunes.models import Emotion


class AnalyticsSerializer(serializers.Serializer):
    emotion_name = serializers.CharField(max_length=20)
    energy = serializers.FloatField(min_value=0, max_value=1)
    valence = serializers.FloatField(min_value=0, max_value=1)
    danceability = serializers.FloatField(min_value=0, max_value=1)
    total_songs = serializers.IntegerField()


class AnalyticsRequestSerializer(serializers.Serializer):
    genre = serializers.CharField(max_length=15, required=False)
    emotion = serializers.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
    context = serializers.ChoiceField(choices=UserSongVote.CONTEXT_CHOICES, required=False)
