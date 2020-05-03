import logging
import random

from django.conf import settings
from django.db import IntegrityError
from django.http import Http404, JsonResponse
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.models import UserSongVote
from accounts.utils import filter_duplicate_votes_on_song_from_playlist
from base.mixins import DeleteRequestValidatorMixin, GetRequestValidatorMixin, PostRequestValidatorMixin
from libs.moody_logging import auto_fingerprint, update_logging_data
from libs.utils import average
from tunes.models import Emotion, Song
from tunes.paginators import PlaylistPaginator
from tunes.serializers import (
    BrowseSongsRequestSerializer,
    DeleteVoteRequestSerializer,
    LastPlaylistSerializer,
    OptionsSerializer,
    PlaylistSongsRequestSerializer,
    SongSerializer,
    VoteSerializer,
    VoteSongsRequestSerializer,
)
from tunes.utils import CachedPlaylistManager, generate_browse_playlist


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

    @update_logging_data
    def filter_queryset(self, queryset, **kwargs):
        cached_playlist_manager = CachedPlaylistManager()
        jitter = self.cleaned_data.get('jitter')
        limit = self.cleaned_data.get('limit') or self.default_limit

        energy = None
        valence = None
        danceability = None
        strategy = random.choice(settings.BROWSE_PLAYLIST_STRATEGIES)

        # Should be able to supply 0 for jitter, so we'll check explicitly for None
        if jitter is None:
            jitter = self.default_jitter

        # Try to use upvotes for this emotion and context to generate attributes for songs to return
        if self.cleaned_data.get('context'):
            votes = self.request.user.usersongvote_set.filter(
                emotion__name=self.cleaned_data['emotion'],
                context=self.cleaned_data['context'],
                vote=True
            )

            if votes.exists():
                attributes_for_votes = average(votes, 'song__valence', 'song__energy', 'song__danceability')
                valence = attributes_for_votes['song__valence__avg']
                energy = attributes_for_votes['song__energy__avg']
                danceability = attributes_for_votes['song__danceability__avg']

        # If context not provided or the previous query on upvotes for context did return any votes,
        # determine attributes from the attributes for the user and emotion
        if energy is None or valence is None or valence is None:
            user_emotion = self.request.user.get_user_emotion_record(self.cleaned_data['emotion'])
            energy = user_emotion.energy
            valence = user_emotion.valence
            danceability = user_emotion.danceability

        logger.info(
            'Generating browse playlist for user {}'.format(self.request.user.username),
            extra={
                'fingerprint': auto_fingerprint('generate_playlist', **kwargs),
                'user_id': self.request.user.pk,
                'emotion': self.cleaned_data['emotion'],
                'genre': self.cleaned_data.get('genre'),
                'context': self.cleaned_data.get('context'),
                'strategy': strategy,
                'energy': energy,
                'valence': valence,
                'danceability': danceability
            }
        )

        playlist = generate_browse_playlist(
            energy,
            valence,
            danceability,
            strategy=strategy,
            limit=limit,
            jitter=jitter,
            songs=queryset
        )

        cached_playlist_manager.cache_browse_playlist(
            self.request.user,
            playlist,
            self.cleaned_data['emotion'],
            self.cleaned_data.get('context'),
            self.cleaned_data.get('description')
        )

        return playlist

    def get_queryset(self):
        queryset = super(BrowseView, self).get_queryset()

        if self.cleaned_data.get('genre'):
            queryset = queryset.filter(genre=self.cleaned_data['genre'])

        user_votes = self.request.user.usersongvote_set.filter(emotion__name=self.cleaned_data['emotion'])

        # If a context is provided, only exclude songs a user has voted on for that context
        # This allows a song to be a candidate for multiple context playlists for a particular emotion
        # Songs in WORK context could also be in PARTY context, maybe?
        if self.cleaned_data.get('context'):
            user_votes = user_votes.filter(context=self.cleaned_data['context'])

        previously_voted_song_ids = user_votes.values_list('song__id', flat=True)

        return queryset.exclude(id__in=previously_voted_song_ids)


class LastPlaylistView(generics.RetrieveAPIView):
    """
    Return a JSON response of the cached user playlist if one exists. If a cached playlist is not found,
    will return a 400 Bad Request.
    """
    serializer_class = LastPlaylistSerializer

    def get_object(self):
        cached_playlist_manager = CachedPlaylistManager()
        cached_playlist = cached_playlist_manager.retrieve_cached_browse_playlist(self.request.user)

        if cached_playlist:
            emotion = cached_playlist['emotion']
            playlist = cached_playlist['playlist']
            context = cached_playlist.get('context')
            description = cached_playlist.get('description')

            # Filter out songs user has already voted on from the playlist
            # to prevent double votes on songs
            user_voted_songs = self.request.user.usersongvote_set.all().values_list('song__code', flat=True)
            playlist = [song for song in playlist if song.code not in user_voted_songs]
            return {
                'emotion': emotion,
                'context': context,
                'description': description,
                'playlist': playlist
            }
        else:
            logger.warning('No cached browse playlist found for user {}'.format(self.request.user.username))
            raise ValidationError({'errors': 'Could not find cached playlist'})


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
            logger.warning(
                'Unable to retrieve song with code {}'.format(self.cleaned_data['song_code']),
                extra={
                    'fingerprint': auto_fingerprint('song_not_found', **kwargs),
                }
            )

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
            logger.info(
                'Saved vote for user {} voting on song {} for emotion {}'.format(
                    self.request.user.username,
                    song.code,
                    emotion.full_name
                ),
                extra={
                    'vote_data': vote_data,
                    'fingerprint': auto_fingerprint('created_new_vote', **kwargs),
                }
            )

            return JsonResponse({'status': 'OK'}, status=status.HTTP_201_CREATED)

        except IntegrityError:
            logger.warning(
                'Bad data supplied to VoteView.create from {}'.format(self.request.user.username),
                extra={
                    'vote_data': vote_data,
                    'fingerprint': auto_fingerprint('bad_vote_data', **kwargs),
                }
            )

            raise ValidationError('Bad data supplied to {}'.format(self.__class__.__name__))

    def destroy(self, request, *args, **kwargs):
        votes = UserSongVote.objects.filter(
            user_id=self.request.user.id,
            emotion__name=self.cleaned_data['emotion'],
            song__code=self.cleaned_data['song_code'],
            vote=True
        )

        if self.cleaned_data.get('context'):
            votes = votes.filter(context=self.cleaned_data['context'])

        if not votes.exists():
            logger.warning(
                'Unable to find UserSongVote to delete',
                extra={
                    'request_data': self.cleaned_data,
                    'fingerprint': auto_fingerprint('unvote_fail_missing_vote', **kwargs),
                }
            )
            raise Http404()

        for vote in votes:
            vote.delete()

            logger.info(
                'Deleted vote for user {} with song {} and emotion {}'.format(
                    self.request.user.username,
                    self.cleaned_data['song_code'],
                    self.cleaned_data['emotion'],
                ),
                extra={
                    'fingerprint': auto_fingerprint('unvote_success', **kwargs),
                    'data': self.cleaned_data
                }
            )

        return JsonResponse({'status': 'OK'})


class PlaylistView(GetRequestValidatorMixin, generics.ListAPIView):
    """
    Returns a JSON response of songs that the user has voted as making them feel a particular emotion (they have voted
    on the songs as making them feel the given emotion.
    """
    serializer_class = VoteSerializer
    queryset = UserSongVote.objects.prefetch_related('emotion', 'song').all()
    pagination_class = PlaylistPaginator

    get_request_serializer = PlaylistSongsRequestSerializer

    def filter_queryset(self, queryset):
        # Find the songs the user has previously voted as making them feel the desired emotion
        emotion = self.cleaned_data['emotion']

        user_votes = queryset.filter(
            user=self.request.user,
            emotion__name=emotion,
            vote=True
        )

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
