from rest_framework import serializers

from accounts.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField()

    class Meta:
        model = UserProfile
        fields = ('has_rejected_spotify_auth', 'user_id')

    def get_user_id(self, obj):
        return obj.user.pk


class UserProfileRequestSerializer(serializers.Serializer):
    has_rejected_spotify_auth = serializers.BooleanField(required=False)
    has_completed_onboarding = serializers.BooleanField(required=False)
