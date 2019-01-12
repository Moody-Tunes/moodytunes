import logging

from django.db import IntegrityError
from django.http import Http404
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.models import UserSongVote
from base.mixins import ValidateRequestDataMixin
from tunes.forms import BrowseSongsForm, VoteSongsForm, PlaylistSongsForm, DeleteVoteForm
from tunes.models import Song, Emotion
from tunes.serializers import SongSerializer
from tunes.utils import generate_browse_playlist

logger = logging.getLogger(__name__)


class BrowseView(ValidateRequestDataMixin, generics.ListAPIView):
    """
    Return a JSON response of Song records that match a given inout query params.
    The main thing that should be passed is an `emotion_name`, which denotes the emotion
    of the songs that should be returned.
    """
    serializer_class = SongSerializer
    queryset = Song.objects.all()

    default_jitter = .25
    default_limit = 10

    get_form = BrowseSongsForm

    def filter_queryset(self, queryset):
        jitter = self.cleaned_data['jitter']
        limit = self.cleaned_data['limit'] or self.default_limit

        # Should be able to supply 0 for jitter, so we'll check explicitly for None
        if jitter is None:
            jitter = self.default_jitter

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

        if self.cleaned_data['genre']:
            queryset = queryset.filter(genre=self.cleaned_data['genre'])

        user_votes = self.request.user.get_user_song_vote_records(self.cleaned_data['emotion'])
        previously_voted_song_ids = [vote.song.id for vote in user_votes]

        return queryset.exclude(id__in=previously_voted_song_ids)


class VoteView(ValidateRequestDataMixin, generics.CreateAPIView, generics.DestroyAPIView):
    post_form = VoteSongsForm
    delete_form = DeleteVoteForm

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

    def destroy(self, request, *args, **kwargs):
        try:
            vote = UserSongVote.objects.get(
                user_id=self.request.user.id,
                emotion__name=self.cleaned_data['emotion'],
                song__code=self.cleaned_data['song_code']
            )

            # TODO: What to do about boundaries for the UserEmotion?
            vote.delete()

            logger.info('Deleted vote for user {} with song {} and emotion {}'.format(
                self.request.user.username,
                self.cleaned_data['emotion'],
                self.cleaned_data['song_code']
            ))

            return Response(status=status.HTTP_204_NO_CONTENT)

        except UserSongVote.DoesNotExist:
            logger.warning('Unable to find UserSongVote to delete', extra={'request_data': self.cleaned_data})
            raise Http404
        except UserSongVote.MultipleObjectsReturned:
            logger.warning('Conflict when trying to delete UserSongVote', extra={'request_dat': self.cleaned_data})
            return Response(status=status.HTTP_409_CONFLICT)


class PlaylistView(ValidateRequestDataMixin, generics.ListAPIView):
    serializer_class = SongSerializer
    queryset = Song.objects.all()

    get_form = PlaylistSongsForm

    def get_queryset(self):
        queryset = super(PlaylistView, self).get_queryset()

        if self.cleaned_data['genre']:
            queryset = queryset.filter(genre=self.cleaned_data['genre'])

        return queryset

    def filter_queryset(self, queryset):
        # Find the songs the user has previously voted as making them feel the desired emotion

        emotion = self.cleaned_data['emotion']

        user_votes_for_emotion = self.request.user.get_user_song_vote_records(emotion)
        desired_songs = [vote.song.id for vote in user_votes_for_emotion if vote.vote]

        return queryset.filter(id__in=desired_songs)
