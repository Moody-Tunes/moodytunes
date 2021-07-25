import json
import logging
import random
import re

from django.conf import settings
from django.db import IntegrityError
from django.http import Http404, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.models import UserSongVote
from base.mixins import DeleteRequestValidatorMixin, GetRequestValidatorMixin, PostRequestValidatorMixin
from libs.moody_logging import auto_fingerprint, update_logging_data
from libs.utils import average
from spotify.models import SpotifyUserData
from tunes.models import Emotion, Song
from tunes.serializers import (
    BrowseSongsRequestSerializer,
    DeleteVoteRequestSerializer,
    LastPlaylistSerializer,
    OptionsSerializer,
    PlaylistSerializer,
    PlaylistSongsRequestSerializer,
    SongSerializer,
    VoteInfoRequestSerializer,
    VoteInfoSerializer,
    VoteSongsRequestSerializer,
)
from tunes.utils import CachedPlaylistManager, filter_duplicate_votes_on_song_from_playlist, generate_browse_playlist


logger = logging.getLogger(__name__)


class BrowseView(GetRequestValidatorMixin, generics.ListAPIView):
    """
    Return a JSON response of Song records that match a given input query params.
    The main thing that should be passed is `emotion`, which is the mood in our
    system the user desires to feel.
    """
    serializer_class = SongSerializer
    queryset = Song.objects.all()

    default_jitter = settings.BROWSE_DEFAULT_JITTER
    default_limit = settings.BROWSE_DEFAULT_LIMIT

    get_request_serializer = BrowseSongsRequestSerializer

    @swagger_auto_schema(query_serializer=BrowseSongsRequestSerializer())
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        resp = super().list(request, *args, **kwargs)
        resp.data.update({'trace_id': request.trace_id})

        return resp

    @update_logging_data
    def filter_queryset(self, queryset, **kwargs):
        cached_playlist_manager = CachedPlaylistManager(self.request.user)
        jitter = self.cleaned_data.get('jitter')
        limit = self.cleaned_data.get('limit') or self.default_limit
        artist = self.cleaned_data.get('artist')

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

            # If the user doesn't have a UserEmotion record for the emotion, fall back to the
            # default attributes for the emotion
            if not user_emotion:
                emotion = Emotion.objects.get(name=self.cleaned_data['emotion'])
                energy = emotion.energy
                valence = emotion.valence
                danceability = emotion.danceability
            else:
                energy = user_emotion.energy
                valence = user_emotion.valence
                danceability = user_emotion.danceability

        # Try to fetch top artists for user from Spotify
        top_artists = None
        try:
            spotify_data = SpotifyUserData.objects.get(spotify_auth__user=self.request.user)
            top_artists = spotify_data.top_artists
        except SpotifyUserData.DoesNotExist:
            pass

        logger.info(
            'Generating {} browse playlist for user {}'.format(
                self.cleaned_data['emotion'],
                self.request.user.username,
            ),
            extra={
                'fingerprint': auto_fingerprint('generate_browse_playlist', **kwargs),
                'user_id': self.request.user.pk,
                'emotion': Emotion.get_full_name_from_keyword(self.cleaned_data['emotion']),
                'genre': self.cleaned_data.get('genre'),
                'context': self.cleaned_data.get('context'),
                'strategy': strategy,
                'energy': energy,
                'valence': valence,
                'danceability': danceability,
                'artist': artist,
                'jitter': jitter,
                'top_artists': top_artists,
                'trace_id': self.request.trace_id,
            }
        )

        playlist = generate_browse_playlist(
            energy,
            valence,
            danceability,
            strategy=strategy,
            limit=limit,
            jitter=jitter,
            artist=artist,
            top_artists=top_artists,
            songs=queryset
        )

        cached_playlist_manager.cache_browse_playlist(
            playlist,
            self.cleaned_data['emotion'],
            self.cleaned_data.get('context'),
            self.cleaned_data.get('description')
        )

        return playlist

    def get_queryset(self):
        queryset = super().get_queryset()

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
    Return a JSON response of the cached user playlist if one exists.
    """
    serializer_class = LastPlaylistSerializer

    @update_logging_data
    def get_object(self, **kwargs):
        cached_playlist_manager = CachedPlaylistManager(self.request.user)
        cached_playlist = cached_playlist_manager.retrieve_cached_browse_playlist()

        if cached_playlist:
            emotion = cached_playlist['emotion']
            playlist = cached_playlist['playlist']
            context = cached_playlist.get('context')
            description = cached_playlist.get('description')

            # Filter out songs user has already voted on from the playlist
            # for the emotion to prevent double votes on songs
            user_voted_songs = self.request.user.usersongvote_set.filter(
                emotion__name=emotion
            ).values_list(
                'song__pk', flat=True
            )

            playlist = [song for song in playlist if song.pk not in user_voted_songs]

            return {
                'emotion': emotion,
                'context': context,
                'description': description,
                'playlist': playlist,
                'trace_id': self.request.trace_id,
            }
        else:
            logger.warning(
                'No cached browse playlist found for user {}'.format(self.request.user.username),
                extra={
                    'fingerprint': auto_fingerprint('no_cached_browse_playlist_found', **kwargs),
                    'trace_id': self.request.trace_id,
                }
            )

            raise Http404('No cached browse playlist found')


class VoteView(PostRequestValidatorMixin, DeleteRequestValidatorMixin, generics.CreateAPIView, generics.DestroyAPIView):
    """
    post: Register a new `UserSongVote` for the given request user, song, and emotion. Optionally include information
    about listening context and description for context.

    delete: Unregister all `UserSongVote` records for the given request user, song, and emotion.
    """
    post_request_serializer = VoteSongsRequestSerializer
    delete_request_serializer = DeleteVoteRequestSerializer

    @swagger_auto_schema(
        request_body=VoteSongsRequestSerializer(),
        responses={status.HTTP_201_CREATED: json.dumps({'status': 'OK'})}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=DeleteVoteRequestSerializer(),
        responses={status.HTTP_200_OK: json.dumps({'status': 'OK'})}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    @update_logging_data
    def create(self, request, *args, **kwargs):
        try:
            song = Song.objects.get(code=self.cleaned_data['song_code'])
        except (Song.DoesNotExist, Song.MultipleObjectsReturned):
            logger.warning(
                'Unable to retrieve song with code {}'.format(self.cleaned_data['song_code']),
                extra={
                    'fingerprint': auto_fingerprint('song_not_found', **kwargs),
                    'trace_id': request.trace_id,
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
            vote = UserSongVote(**vote_data)
            vote._trace_id = request.trace_id
            vote.save()

            logger.info(
                'Saved vote for user {} voting on song {} for emotion {}'.format(
                    self.request.user.username,
                    song.code,
                    emotion.full_name
                ),
                extra={
                    'vote_data': vote_data,
                    'emotion': emotion.full_name,
                    'vote_id': vote.pk,
                    'fingerprint': auto_fingerprint('created_new_vote', **kwargs),
                    'trace_id': request.trace_id,
                }
            )

            return JsonResponse({'status': 'OK'}, status=status.HTTP_201_CREATED)

        except IntegrityError as exc:
            logger.warning(
                'Bad data supplied to VoteView.create from {}'.format(self.request.user.username),
                extra={
                    'vote_data': vote_data,
                    'fingerprint': auto_fingerprint('bad_vote_data', **kwargs),
                    'exception_info': exc,
                    'trace_id': request.trace_id,
                }
            )

            raise ValidationError('Bad data supplied to {}'.format(self.__class__.__name__))

    @update_logging_data
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
                    'trace_id': request.trace_id,
                }
            )

            raise Http404()

        for vote in votes:
            vote._trace_id = request.trace_id
            vote.delete()

            logger.info(
                'Deleted vote for user {} with song {} and emotion {} and context {}'.format(
                    self.request.user.username,
                    self.cleaned_data['song_code'],
                    Emotion.get_full_name_from_keyword(self.cleaned_data['emotion']),
                    vote.context or 'None',
                ),
                extra={
                    'fingerprint': auto_fingerprint('unvote_success', **kwargs),
                    'vote_id': vote.pk,
                    'data': self.cleaned_data,
                    'trace_id': request.trace_id,
                }
            )

        return JsonResponse({'status': 'OK'})


class PlaylistView(GetRequestValidatorMixin, generics.ListAPIView):
    """
    Returns a JSON response of songs that the user has voted as making them feel a desired emotion.
    """
    serializer_class = PlaylistSerializer
    queryset = UserSongVote.objects.all()

    get_request_serializer = PlaylistSongsRequestSerializer

    @swagger_auto_schema(query_serializer=PlaylistSongsRequestSerializer())
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @update_logging_data
    def list(self, request, *args, **kwargs):
        logger.info(
            'Generating {} emotion playlist for user {}'.format(
                self.cleaned_data['emotion'],
                self.request.user.username,
            ),
            extra={
                'fingerprint': auto_fingerprint('generate_emotion_playlist', **kwargs),
                'user_id': self.request.user.pk,
                'emotion': Emotion.get_full_name_from_keyword(self.cleaned_data['emotion']),
                'genre': self.cleaned_data.get('genre'),
                'context': self.cleaned_data.get('context'),
                'artist': self.cleaned_data.get('artist'),
                'page': self.request.GET.get('page'),
                'trace_id': request.trace_id,
            }
        )

        resp = super().list(request, *args, **kwargs)

        first_page = last_page = None

        if resp.data['previous']:
            first_page = re.sub(r'&page=[0-9]*', '', resp.data['previous'])

        if resp.data['next']:
            last_page = re.sub(r'page=[0-9]*', 'page=last', resp.data['next'])

        queryset = self.filter_queryset(self.get_queryset())

        # Update response data with analytics for emotion
        votes_for_emotion_data = average(queryset, 'song__valence', 'song__energy', 'song__danceability')
        valence = votes_for_emotion_data['song__valence__avg']
        energy = votes_for_emotion_data['song__energy__avg']
        danceability = votes_for_emotion_data['song__danceability__avg']

        resp.data.update({
            'valence': valence,
            'energy': energy,
            'danceability': danceability,
            'emotion_name': Emotion.get_full_name_from_keyword(self.cleaned_data['emotion']),
            'first_page': first_page,
            'last_page': last_page,
        })

        return resp

    def filter_queryset(self, queryset):
        if self.cleaned_data.get('genre'):
            queryset = queryset.filter(song__genre=self.cleaned_data['genre'])

        if self.cleaned_data.get('context'):
            queryset = queryset.filter(context=self.cleaned_data['context'])

        if self.cleaned_data.get('artist'):
            queryset = queryset.filter(song__artist__icontains=self.cleaned_data['artist'])

        return filter_duplicate_votes_on_song_from_playlist(queryset)

    def get_queryset(self):
        queryset = super().get_queryset()

        return queryset.filter(
            user=self.request.user,
            emotion__name=self.cleaned_data['emotion'],
            vote=True
        )


class OptionView(generics.GenericAPIView):
    """
    Returns a JSON response of available site options. This returns the emotions we have in our system, as well as the
    different genres of songs in our database.
    """
    serializer_class = OptionsSerializer

    pagination_class = None

    @method_decorator(cache_page(settings.OPTIONS_CACHE_TIMEOUT))
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


class VoteInfoView(GetRequestValidatorMixin, generics.RetrieveAPIView):
    """
    Returns a JSON response of info on votes for a given user, emotion, and song. Currently used to
    find the different contexts for a song that a user has voted on.
    """
    serializer_class = VoteInfoSerializer

    get_request_serializer = VoteInfoRequestSerializer

    @swagger_auto_schema(query_serializer=VoteInfoRequestSerializer())
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        contexts = UserSongVote.objects.filter(
            user=self.request.user,
            emotion__name=self.cleaned_data['emotion'],
            song__code=self.cleaned_data['song_code'],
        ).values_list(
            'context',
            flat=True,
        )

        return {'contexts': contexts}
