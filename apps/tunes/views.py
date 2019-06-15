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
    LastPlaylistSerializer
)
from tunes.utils import CachedPlaylistManager, generate_browse_playlist
from libs.utils import average

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
        cached_playlist_manager = CachedPlaylistManager()
        jitter = self.cleaned_data.get('jitter')
        limit = self.cleaned_data.get('limit') or self.default_limit
        energy = None
        valence = None

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
                energy = average(votes.values_list('song__energy', flat=True))
                valence = average(votes.values_list('song__valence', flat=True))

        # If context not provided or the previous query on upvotes for context did return any votes,
        # determine attributes from the attributes for the user and emotion
        if energy is None or valence is None:
            user_emotion = self.request.user.get_user_emotion_record(self.cleaned_data['emotion'])
            energy = user_emotion.energy
            valence = user_emotion.valence

        playlist = generate_browse_playlist(
            energy,
            valence,
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
                    'fingerprint': 'tunes.VoteView.create.song_not_found'
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
                'Saved vote for user {} voting on song {}'.format(
                    self.request.user.username,
                    song.code,
                ),
                extra={
                    'vote_data': vote_data,
                    'fingerprint': 'tunes.VoteView.create.created_new_vote'
                }
            )

            return JsonResponse({'status': 'OK'}, status=status.HTTP_201_CREATED)

        except IntegrityError:
            logger.warning(
                'Bad data supplied to VoteView.create from {}'.format(self.request.user.username),
                extra={
                    'vote_data': vote_data,
                    'fingerprint': 'tunes.VoteView.create.bad_vote_data'
                }
            )

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
