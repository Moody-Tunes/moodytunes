import logging

from django.db import IntegrityError
from django.http import Http404, JsonResponse
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.models import UserSongVote
from accounts.utils import filter_duplicate_votes_on_song_from_playlist
from base.mixins import (
    GetRequestValidatorMixin,
    PostRequestValidatorMixin,
    DeleteRequestValidatorMixin
)
from tunes.models import Song, Emotion
from tunes.paginators import PlaylistPaginator
from tunes.serializers import (
    OptionsSerializer,
    SongSerializer,
    VoteSerializer,
    BrowseSongsRequestSerializer,
    DeleteVoteRequestSerializer,
    PlaylistSongsRequestSerializer,
    VoteSongsRequestSerializer,
)
from tunes.utils import generate_browse_playlist

logger = logging.getLogger(__name__)


class BrowseView(GetRequestValidatorMixin, generics.ListAPIView):
    """
    Return a JSON response of Song records that match a given input query params.
    The main thing that should be passed is an `emotion_name`, which denotes the emotion
    of the songs that the user wants to feel.
    """
    serializer_class = SongSerializer
    queryset = Song.objects.all()

    default_jitter = .15
    default_limit = 9

    get_request_serializer = BrowseSongsRequestSerializer

    def filter_queryset(self, queryset):
        jitter = self.cleaned_data.get('jitter')
        limit = self.cleaned_data.get('limit') or self.default_limit

        # Should be able to supply 0 for jitter, so we'll check explicitly for None
        if jitter is None:
            jitter = self.default_jitter

        user_emotion = self.request.user.get_user_emotion_record(self.cleaned_data['emotion'])

        return generate_browse_playlist(
            user_emotion.energy,
            user_emotion.valence,
            limit=limit,
            jitter=jitter,
            songs=queryset
        )

    def get_queryset(self):
        queryset = super(BrowseView, self).get_queryset()

        if self.cleaned_data.get('genre'):
            queryset = queryset.filter(genre=self.cleaned_data['genre'])

        user_votes = self.request.user.usersongvote_set.filter(emotion__name=self.cleaned_data['emotion'])

        # If a context is provided, only exclude songs a user has voted on for that context
        # This allows a song to be a candidate for multiple playlists
        # Songs in WORK context could  also be in PARTY context, maybe?
        if self.cleaned_data.get('context'):
            user_votes = user_votes.filter(context=self.cleaned_data['context'])

        previously_voted_song_ids = user_votes.values_list('song__id', flat=True)

        return queryset.exclude(id__in=previously_voted_song_ids)


class VoteView(PostRequestValidatorMixin, DeleteRequestValidatorMixin, generics.CreateAPIView, generics.DestroyAPIView):
    """
    POST: Register a new `UserSongVote` for the given request user, song, and emotion; denotes whether or not the song
    made the user feel that emotion.
    DELETE: Unregister a `UserSongVote` for the given request user, song, and emotion; marks the song as not making the
    user feel that emotion.
    """
    post_request_serializer = VoteSongsRequestSerializer
    delete_request_serializer = DeleteVoteRequestSerializer

    def create(self, request, *args, **kwargs):
        try:
            song = Song.objects.get(code=self.cleaned_data['song_code'])
        except (Song.DoesNotExist, Song.MultipleObjectsReturned):
            logger.warning('Unable to retrieve song with code {}'.format(self.cleaned_data['song_code']))

            raise Http404('No song exists with code: {}'.format(self.cleaned_data['song_code']))

        emotion = Emotion.objects.get(name=self.cleaned_data['emotion'])

        vote_data = {
            'user_id': self.request.user.id,
            'emotion_id': emotion.id,
            'song_id': song.id,
            'vote': self.cleaned_data['vote'],
            'context': self.cleaned_data.get('context', ''),
            'description': self.cleaned_data.get('description', '')
        }

        try:
            UserSongVote.objects.create(**vote_data)
            logger.info('Saved vote for user {} voting on song {} with desired emotion {}. Outcome: {}'.format(
                self.request.user.username,
                song.code,
                self.cleaned_data['emotion'],
                vote_data['vote']
            ))

            return JsonResponse({'status': 'OK'}, status=status.HTTP_201_CREATED)

        except IntegrityError:
            logger.warning('Bad data supplied to VoteView.create: {}'.format(vote_data))

            raise ValidationError('Bad data supplied to {}'.format(self.__class__.__name__))

    def destroy(self, request, *args, **kwargs):
        try:
            votes = UserSongVote.objects.filter(
                user_id=self.request.user.id,
                emotion__name=self.cleaned_data['emotion'],
                song__code=self.cleaned_data['song_code'],
                vote=True
            )

            if self.cleaned_data.get('context'):
                votes = votes.filter(context=self.cleaned_data['context'])

            if not votes.exists():
                raise UserSongVote.DoesNotExist()

            for vote in votes:
                vote.delete()

                logger.info('Deleted vote for user {} with song {} and emotion {}; Context: {}'.format(
                    self.request.user.username,
                    self.cleaned_data['song_code'],
                    self.cleaned_data['emotion'],
                    self.cleaned_data.get('context'),
                ))

            return JsonResponse({'status': 'OK'})

        except UserSongVote.DoesNotExist:
            logger.warning('Unable to find UserSongVote to delete', extra={'request_data': self.cleaned_data})
            raise Http404


class PlaylistView(GetRequestValidatorMixin, generics.ListAPIView):
    """
    Returns a JSON response of songs that the user has voted as making them feel a particular emotion (they have voted
    on the songs as making them feel the given emotion.
    """
    serializer_class = VoteSerializer
    queryset = UserSongVote.objects.all()
    pagination_class = PlaylistPaginator

    get_request_serializer = PlaylistSongsRequestSerializer

    def filter_queryset(self, queryset):
        # Find the songs the user has previously voted as making them feel the desired emotion
        emotion = self.cleaned_data['emotion']

        user_votes = queryset.filter(
            user=self.request.user,
            emotion__name=emotion,
            vote=True
        ).order_by('created')

        return filter_duplicate_votes_on_song_from_playlist(user_votes)

    def get_queryset(self):
        queryset = super(PlaylistView, self).get_queryset()

        if self.cleaned_data.get('genre'):
            queryset = queryset.filter(song__genre=self.cleaned_data['genre'])

        if self.cleaned_data.get('context'):
            queryset = queryset.filter(context=self.cleaned_data['context'])

        return queryset


class OptionView(generics.GenericAPIView):
    """
    Returns a JSON response of available site options. This returns the emotions we have in our system, as well as the
    different genres of songs in our database.
    """
    serializer_class = OptionsSerializer

    def get(self, request, *args, **kwargs):
        # Build map of emotions including code name and display name
        emotion_choices = []
        for emotion in Emotion.objects.all():
            emotion_choices.append({
                'name': emotion.full_name,
                'code': emotion.name
            })

        # Build map of vote context choices
        context_choices = []
        for choice in UserSongVote.CONTEXT_CHOICES:
            name, full_name = choice
            context_choices.append({
                'name': full_name,
                'code': name
            })

        # Retrieve list of song genres
        genre_choices = Song.objects.all().values_list('genre', flat=True).distinct()

        data = {
            'emotions': emotion_choices,
            'genres': genre_choices,
            'contexts': context_choices
        }

        serializer = self.serializer_class(data=data)

        return Response(data=serializer.initial_data)
