import logging

from django.core.exceptions import SuspiciousOperation
from rest_framework import generics

from tunes.forms import BrowseSongsForm
from tunes.serializers import SongSerializer
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

    def __init__(self):
        self.cleaned_data = {}  # Cleaned GET data for query
        super(BrowseView, self).__init__()

    def get_queryset(self):
        user = self.request.user

        emotion = self.cleaned_data['emotion']
        jitter = self.cleaned_data['jitter']
        limit = self.cleaned_data['limit'] or self.default_limit

        # Should be able to supply 0 for jitter, so we'll check explicitly for None
        if jitter is None:
            jitter = self.default_jitter

        user_emotion = user.get_user_emotion_record(emotion)

        # TODO: Refactor to use prefetch helper when we create one
        previously_seen_song_ids = user.usersongvote_set.all().values_list('song__id', flat=True)

        playlist = generate_browse_playlist(
            user_emotion.lower_bound,
            user_emotion.upper_bound,
            exclude_ids=previously_seen_song_ids,
            limit=limit,
            jitter=float(jitter)
        )

        return playlist

    def get(self, request, *args, **kwargs):
        form = BrowseSongsForm(request.GET)

        if form.is_valid():
            self.cleaned_data = form.cleaned_data
            return super().get(request, *args, **kwargs)

        else:
            self.logger.warning('Invalid data supplied to BrowseView.get: {}'.format(request.GET))

            raise SuspiciousOperation('Invalid GET data supplied to {}'.format(self.__class__.__name__))
