from django.utils.functional import lazy
from rest_framework import serializers

from tunes.models import Emotion
from tunes.utils import get_available_genres


class AnalyticsSerializer(serializers.Serializer):
    emotion = serializers.CharField(min_length=3, max_length=3)
    emotion_name = serializers.CharField(max_length=20)
    genre = serializers.CharField(max_length=15, required=False)
    lower_bound = serializers.FloatField(min_value=0, max_value=1)
    upper_bound = serializers.FloatField(min_value=0, max_value=1)
    average_energy = serializers.FloatField(min_value=0, max_value=1)
    average_valence = serializers.FloatField(min_value=0, max_value=1)
    total_songs = serializers.IntegerField()


class AnalyticsRequestSerializer(serializers.Serializer):
    genre = serializers.ChoiceField(choices=lazy(get_available_genres, tuple)(), required=False)
    emotion = serializers.ChoiceField(choices=Emotion.EMOTION_NAME_CHOICES)
