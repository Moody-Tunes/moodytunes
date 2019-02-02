import logging

from django.db import IntegrityError
from django.http import Http404, JsonResponse
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.models import UserSongVote
from base.mixins import (
    GetRequestValidatorMixin,
    PostRequestValidatorMixin,
    DeleteRequestValidatorMixin
)
from tunes.models import Song, Emotion
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

    default_jitter = .05
    default_limit = 10

    get_request_serializer = BrowseSongsRequestSerializer

    def _set_situation_data(self):
        # Assign context data to request session if present
        context_session_key =  '{}_context'.format(self.cleaned_data['emotion'])
        description_session_key =  '{}_description'.format(self.cleaned_data['emotion'])

        if self.cleaned_data.get('context'):
            self.request.session[context_session_key] = self.cleaned_data['context']

        if self.cleaned_data.get('description'):
            self.request.session[description_session_key] = self.cleaned_data['description']

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
        self._set_situation_data()
        queryset = super(BrowseView, self).get_queryset()

        if self.cleaned_data.get('genre'):
            queryset = queryset.filter(genre=self.cleaned_data['genre'])

        user_votes = self.request.user.get_user_song_vote_records(self.cleaned_data['emotion'])
        previously_voted_song_ids = [vote.song.id for vote in user_votes]

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
            'context': request.session.get('{}_context'.format(self.cleaned_data['emotion']), ''),
            'description': request.session.get('{}_description'.format(self.cleaned_data['emotion']), '')
        }

        try:
            UserSongVote.objects.create(**vote_data)
            logger.info('Saved vote for user {} voting on song {} with desired emotion {}. Outcome: {}'.format(
                self.request.user.username,
                song.code,
                emotion.full_name,
                vote_data['vote']
            ))

            return JsonResponse({'status': 'OK'}, status=status.HTTP_201_CREATED)

        except IntegrityError:
            logger.warning('Bad data supplied to VoteView.create: {}'.format(vote_data))

            raise ValidationError('Bad data supplied to {}'.format(self.__class__.__name__))

    def destroy(self, request, *args, **kwargs):
        try:
            vote = UserSongVote.objects.get(
                user_id=self.request.user.id,
                emotion__name=self.cleaned_data['emotion'],
                song__code=self.cleaned_data['song_code']
            )

            vote.delete()

            logger.info('Deleted vote for user {} with song {} and emotion {}'.format(
                self.request.user.username,
                self.cleaned_data['emotion'],
                self.cleaned_data['song_code']
            ))

            return JsonResponse({'status': 'OK'}, status=status.HTTP_204_NO_CONTENT)

        except UserSongVote.DoesNotExist:
            logger.warning('Unable to find UserSongVote to delete', extra={'request_data': self.cleaned_data})
            raise Http404
        except UserSongVote.MultipleObjectsReturned:
            logger.warning('Conflict when trying to delete UserSongVote', extra={'request_data': self.cleaned_data})
            return Response(status=status.HTTP_409_CONFLICT)


class PlaylistView(GetRequestValidatorMixin, generics.ListAPIView):
    """
    Returns a JSON response of songs that the user has voted as making them feel a particular emotion (they have voted
    on the songs as making them feel the given emotion.
    """
    serializer_class = VoteSerializer
    queryset = UserSongVote.objects.all()

    get_request_serializer = PlaylistSongsRequestSerializer

    def filter_queryset(self, queryset):
        # Find the songs the user has previously voted as making them feel the desired emotion
        emotion = self.cleaned_data['emotion']

        return queryset.filter(
            user=self.request.user,
            emotion__name=emotion,
            vote=True
        )

    def get_queryset(self):
        queryset = super(PlaylistView, self).get_queryset()

        if self.cleaned_data.get('genre'):
            queryset = queryset.filter(song__genre=self.cleaned_data['genre'])

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

        # Retrieve list of song genres
        genre_choices = Song.objects.all().values_list('genre', flat=True).distinct()

        data = {
            'emotions': emotion_choices,
            'genres': genre_choices
        }

        serializer = self.serializer_class(data=data)

        return Response(data=serializer.initial_data)
