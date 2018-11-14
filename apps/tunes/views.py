from rest_framework import generics

from tunes.serializers import SongSerializer
from tunes.models import Song
from tunes.utils import generate_browse_playlist


class BrowseView(generics.ListAPIView):
    """
    Return a JSON response of Song records that match a given inout query params.
    The main thing that should be passed is an `emotion_name`, which denotes the emotion
    of the songs that should be returned.
    """
    serializer_class = SongSerializer

    def get_queryset(self):
        user = self.request.user
        emotion = self.request.GET.get('emotion_name')

        user_emotion = user.get_user_emotion_record(emotion)

        if not user_emotion:
            return Song.objects.none()

        # TODO: Refactor to use prefetch helper when we create one
        previously_seen_song_ids = user.usersongvote_set.all().values_list('song__id', flat=True)

        # TODO: Get rid of magic numbers
        playlist = generate_browse_playlist(
            user_emotion.lower_bound,
            user_emotion.upper_bound,
            exclude_ids=previously_seen_song_ids,
            limit=10,
            jitter=.25
        )

        return playlist
