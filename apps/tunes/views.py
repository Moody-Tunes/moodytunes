import logging

from django.core.exceptions import SuspiciousOperation
from django.db import IntegrityError
from django.http import Http404
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.models import UserSongVote
from tunes.forms import BrowseSongsForm, VoteSongsForm, PlaylistSongsForm
from tunes.models import Song, Emotion
from tunes.serializers import SongSerializer
from tunes.utils import generate_browse_playlist

logger = logging.getLogger(__name__)


class BrowseView(generics.ListAPIView):
    """
    Return a JSON response of Song records that match a given inout query params.
    The main thing that should be passed is an `emotion_name`, which denotes the emotion
    of the songs that should be returned.
    """
    serializer_class = SongSerializer
    queryset = Song.objects.all()

    default_jitter = .25
    default_limit = 10

    def __init__(self):
        self.cleaned_data = {}  # Cleaned GET data for query
        super(BrowseView, self).__init__()

    def filter_queryset(self, queryset):
        jitter = self.cleaned_data['jitter']
        limit = self.cleaned_data['limit'] or self.default_limit

        # Should be able to supply 0 for jitter, so we'll check explicitly for None
        if jitter is None:
            jitter = self.default_jitter

        # `emotion` is assured to be a valid Emotion name because the form
        # we use to clean the data to this view validates that `emotion`
        # is mapped to a record in our database
        user_emotion = self.request.user.get_user_emotion_record(self.cleaned_data['emotion'])

        return generate_browse_playlist(
            user_emotion.lower_bound,
            user_emotion.upper_bound,
            limit=limit,
            jitter=float(jitter),
            songs=queryset
        )

    def get_queryset(self):
        queryset = super(BrowseView, self).get_queryset()

        # Exclude songs a user has previously voted on for the given emotion
        # ex. if the user voted on a song when asking for Melancholy songs, it
        # should still be a candidate if the user then asks for Happy songs
        user_votes = self.request.user.get_user_song_vote_records(self.cleaned_data['emotion'])
        previously_voted_song_ids = [vote.song.id for vote in user_votes]

        return queryset.exclude(id__in=previously_voted_song_ids)

    def get(self, request, *args, **kwargs):
        form = BrowseSongsForm(request.GET)

        if form.is_valid():
            self.cleaned_data = form.cleaned_data
            return super().get(request, *args, **kwargs)

        else:
            logger.warning('Invalid data supplied to BrowseView.get: {}'.format(request.GET))

            raise SuspiciousOperation('Invalid GET data supplied to {}'.format(self.__class__.__name__))


class VoteView(generics.CreateAPIView):
    def __init__(self):
        self.cleaned_data = {}  # Cleaned POST data for request
        super(VoteView, self).__init__()

    def create(self, request, *args, **kwargs):
        try:
            song = Song.objects.get(code=self.cleaned_data['song_code'])
        except (Song.DoesNotExist, Song.MultipleObjectsReturned):
            logger.warning('Unable to retrieve song with code {}'.format(self.cleaned_data['song_code']))

            raise Http404('No song exists with code: {}'.format(self.cleaned_data['song_code']))

        # `emotion` is assured to be a valid Emotion name because the form
        # we use to clean the data to this view validates that `emotion`
        # is mapped to a record in our database
        emotion = Emotion.objects.get(name=self.cleaned_data['emotion'])

        vote_data = {
            'user_id': self.request.user.id,
            'emotion_id': emotion.id,
            'song_id': song.id,
            'vote': self.cleaned_data['vote']
        }

        try:
            UserSongVote.objects.create(**vote_data)
            logger.info('Saved vote for user {} voting on song {} with desired emotion {}. Outcome: {}'.format(
                self.request.user.username,
                song.code,
                emotion.full_name,
                vote_data['vote']
            ))

            return Response(status=status.HTTP_201_CREATED)

        except IntegrityError:
            logger.warning('Bad data supplied to VoteView.create: {}'.format(vote_data))

            raise ValidationError('Bad data supplied to {}'.format(self.__class__.__name__))

    def post(self, request, *args, **kwargs):
        form = VoteSongsForm(request.POST)

        if form.is_valid():
            self.cleaned_data = form.cleaned_data

            return super(VoteView, self).post(request, *args, **kwargs)

        else:
            logger.warning('Invalid POST data supplied to VoteView.post: {}'.format(request.POST))

            raise SuspiciousOperation('Invalid POST data supplied to {}'.format(self.__class__.__name__))


class PlaylistView(generics.ListAPIView):
    serializer_class = SongSerializer
    queryset = Song.objects.all()

    def __init__(self):
        self.cleaned_data = {}  # Cleaned GET data for query
        super(PlaylistView, self).__init__()

    def get_queryset(self):
        queryset = super(PlaylistView, self).get_queryset()

        if self.cleaned_data['genre']:
            queryset = queryset.filter(genre=self.cleaned_data['genre'])

        return queryset

    def filter_queryset(self, queryset):
        # Find the songs the user has previously voted as making them feel the desired emotion

        # `emotion` is assured to be a valid Emotion name because the form
        # we use to clean the data to this view validates that `emotion`
        # is mapped to a record in our database
        emotion = self.cleaned_data['emotion']

        user_votes_for_emotion = self.request.user.get_user_song_vote_records(emotion)
        desired_songs = [vote.song.id for vote in user_votes_for_emotion if vote.vote]

        return queryset.filter(id__in=desired_songs)

    def get(self, request, *args, **kwargs):
        form = PlaylistSongsForm(request.GET)

        if form.is_valid():
            self.cleaned_data = form.cleaned_data
            return super().get(request, *args, **kwargs)

        else:
            logger.warning('Invalid data supplied to PlaylistView.get: {}'.format(request.GET))

            raise SuspiciousOperation('Invalid GET data supplied to {}'.format(self.__class__.__name__))
