import logging

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from tunes.forms import BrowseSongsForm
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
    logger = logging.getLogger(__name__)
    default_jitter = .25
    default_limit = 10

    def get_queryset(self):
        user = self.request.user

        # Note: This data has already been cleaned in `get`
        emotion = self.request.GET['emotion']
        jitter = self.request.GET.get('jitter', self.default_jitter)

        user_emotion = user.get_user_emotion_record(emotion)

        # TODO: Refactor to use prefetch helper when we create one
        previously_seen_song_ids = user.usersongvote_set.all().values_list('song__id', flat=True)

        playlist = generate_browse_playlist(
            user_emotion.lower_bound,
            user_emotion.upper_bound,
            exclude_ids=previously_seen_song_ids,
            limit=self.default_limit,
            jitter=float(jitter)
        )

        return playlist

    def get(self, request, *args, **kwargs):
        form = BrowseSongsForm(request.GET)

        if form.is_valid():
            return super().get(request, *args, **kwargs)

        else:
            self.logger.warning('Invalid data supplied to BrowseView.get: {}'.format(request.GET))

            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Invalid data'})
