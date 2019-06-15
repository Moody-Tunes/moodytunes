from unittest import mock

from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import UserSongVote
from tunes.models import Emotion, Song
from tunes.views import BrowseView
from libs.tests.helpers import MoodyUtil
from libs.utils import average


class TestBrowseView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.api_client = APIClient()
        cls.url = reverse('tunes:browse')
        cls.user = MoodyUtil.create_user()

    def setUp(self):
        self.api_client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    def test_unauthenticated_request_is_forbidden(self):
        self.api_client.logout()

        params = {'emotion': Emotion.HAPPY}
        resp = self.api_client.get(self.url, data=params)

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_query_params_passed_returns_bad_request(self):
        resp = self.api_client.get(self.url)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_emotion_passed_returns_bad_request(self):
        params = {'emotion': 'unknown'}
        resp = self.api_client.get(self.url, data=params)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_happy_path(self):
        song = MoodyUtil.create_song()
        params = {
            'emotion': Emotion.HAPPY,
            'jitter': 0
        }

        resp = self.api_client.get(self.url, data=params)
        resp_song = resp.json()[0]

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_song['code'], song.code)

    def test_filter_on_genre(self):
        MoodyUtil.create_song()
        expected_song = MoodyUtil.create_song(genre='super-dope')
        params = {
            'emotion': Emotion.HAPPY,
            'jitter': 0,
            'genre': expected_song.genre
        }

        resp = self.api_client.get(self.url, data=params)
        resp_song = resp.json()[0]

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_song['code'], expected_song.code)

    def test_playlist_respects_limit(self):
        for _ in range(10):
            MoodyUtil.create_song()

        params = {
            'emotion': Emotion.HAPPY,
            'jitter': 0,
            'limit': 5
        }

        resp = self.api_client.get(self.url, data=params)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_data), params['limit'])

    @mock.patch('tunes.views.generate_browse_playlist')
    def test_playlist_uses_default_jitter_if_not_provided(self, mock_generate_playlist):
        song = MoodyUtil.create_song()
        mock_generate_playlist.return_value = [song]

        params = {'emotion': Emotion.HAPPY}
        self.api_client.get(self.url, data=params)

        call_kwargs = mock_generate_playlist.mock_calls[0][2]
        called_jitter = call_kwargs['jitter']

        self.assertEqual(called_jitter, BrowseView.default_jitter)

    def test_playlist_excludes_previously_voted_songs(self):
        voted_song = MoodyUtil.create_song()
        not_voted_song = MoodyUtil.create_song()

        UserSongVote.objects.create(
            user=self.user,
            song=voted_song,
            emotion=Emotion.objects.get(name=Emotion.HAPPY),
            vote=True
        )

        params = {
            'emotion': Emotion.HAPPY,
            'jitter': 0
        }

        resp = self.api_client.get(self.url, data=params)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_data), 1)
        self.assertEqual(resp_data[0]['code'], not_voted_song.code)

    def test_playlist_returns_songs_voted_on_in_a_different_context(self):
        song = MoodyUtil.create_song()

        UserSongVote.objects.create(
            user=self.user,
            song=song,
            emotion=Emotion.objects.get(name=Emotion.HAPPY),
            vote=False,
            context='WORK'
        )

        params = {
            'emotion': Emotion.HAPPY,
            'jitter': 0,
            'context': 'PARTY'
        }

        resp = self.api_client.get(self.url, data=params)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_data), 1)
        self.assertEqual(resp_data[0]['code'], song.code)

    @mock.patch('tunes.views.generate_browse_playlist')
    def test_playlist_for_context_is_generated_with_upvoted_song_attributes_for_context(self, mock_generate_playlist):
        context = 'WORK'
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        song = MoodyUtil.create_song(energy=.5, valence=.75)
        upvote_song_for_context = MoodyUtil.create_song(energy=.75, valence=.95)
        downvote_song_for_context = MoodyUtil.create_song(energy=.6, valence=.75)
        mock_generate_playlist.return_value = [upvote_song_for_context]

        MoodyUtil.create_user_song_vote(self.user, song, emotion, True)
        MoodyUtil.create_user_song_vote(self.user, upvote_song_for_context, emotion, True, context=context)
        MoodyUtil.create_user_song_vote(self.user, downvote_song_for_context, emotion, False, context=context)

        params = {
            'emotion': emotion.name,
            'jitter': 0,
            'context': context
        }
        self.api_client.get(self.url, data=params)

        call_args = mock_generate_playlist.mock_calls[0][1]
        called_energy = call_args[0]
        called_valence = call_args[1]

        self.assertEqual(called_energy, upvote_song_for_context.energy)
        self.assertEqual(called_valence, upvote_song_for_context.valence)


class TestLastPlaylistView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('tunes:last')
        cls.api_client = APIClient()
        cls.user = MoodyUtil.create_user()
        cls.song = MoodyUtil.create_song()

    def setUp(self):
        self.api_client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    @mock.patch('tunes.utils.cache')
    def test_passing_use_cached_playlist_parameter_returns_cached_playlist(self, mock_cache):
        cached_data = {
            'emotion': Emotion.HAPPY,
            'context': 'WORK',
            'songs': Song.objects.all()
        }
        mock_cache.get.return_value = cached_data

        resp = self.api_client.get(self.url)
        resp_json = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_json['playlist'][0]['code'], self.song.code)
        self.assertEqual(resp_json['emotion'], cached_data['emotion'])
        self.assertEqual(resp_json['context'], cached_data['context'])

    @mock.patch('tunes.utils.cache')
    def test_passing_use_cached_playlist_parameter_returns_bad_request_if_no_playlist_found(self, mock_cache):
        mock_cache.get.return_value = None
        expected_error = 'Could not find cached playlist'

        params = {'return_last': True}
        resp = self.api_client.get(self.url, params)
        resp_json = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp_json['errors'], expected_error)

    @mock.patch('tunes.utils.cache')
    def test_cached_playlist_filters_songs_user_voted_on(self, mock_cache):
        voted_song = MoodyUtil.create_song()
        cached_data = {
            'emotion': Emotion.HAPPY,
            'context': 'WORK',
            'songs': Song.objects.all()
        }
        mock_cache.get.return_value = cached_data

        MoodyUtil.create_user_song_vote(
            self.user,
            voted_song,
            Emotion.objects.get(name=Emotion.HAPPY),
            True
        )

        params = {'return_last': True}
        resp = self.api_client.get(self.url, params)
        resp_json = resp.json()

        self.assertNotIn(voted_song, resp_json['playlist'])


class TestVoteView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.api_client = APIClient()
        cls.url = reverse('tunes:vote')
        cls.user = MoodyUtil.create_user()
        cls.song = MoodyUtil.create_song()

    def setUp(self):
        self.api_client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    def test_unauthenticated_request_is_forbidden(self):
        self.api_client.logout()

        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code,
            'vote': True
        }
        resp = self.api_client.post(self.url, data=data, format='json')

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_post_data_passed_returns_bad_request(self):
        resp = self.api_client.post(self.url)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_delete_data_passed_returns_bad_request(self):
        resp = self.api_client.delete(self.url)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_happy_path(self):
        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code,
            'vote': True
        }
        resp = self.api_client.post(self.url, data=data, format='json')

        vote_created = UserSongVote.objects.filter(
            user=self.user,
            emotion__name=Emotion.HAPPY,
            song=self.song,
            vote=True
        ).exists()

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(vote_created)

    def test_bad_request_if_invalid_data_sent(self):
        # Missing vote value
        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code,
        }
        resp = self.api_client.post(self.url, data=data, format='json')

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bad_request_if_bad_emotion_sent(self):
        data = {
            'emotion': 'Bad emotion',
            'song_code': self.song.code,
            'vote': True
        }
        resp = self.api_client.post(self.url, data=data, format='json')

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bad_request_if_bad_song_code_sent(self):
        data = {
            'emotion': Emotion.HAPPY,
            'song_code': 'Bad song code',
            'vote': True
        }
        resp = self.api_client.post(self.url, data=data, format='json')

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_upvoting_on_song_updates_user_emotion_attributes(self):
        user_emotion = self.user.useremotion_set.get(emotion__name=Emotion.HAPPY)
        new_song = MoodyUtil.create_song(energy=.75, valence=.65)

        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code,
            'vote': True
        }
        self.api_client.post(self.url, data=data, format='json')

        data = {
            'emotion': Emotion.HAPPY,
            'song_code': new_song.code,
            'vote': True
        }
        self.api_client.post(self.url, data=data, format='json')

        user_emotion.refresh_from_db()
        expected_energy = average([self.song.energy, new_song.energy])
        expected_valence = average([self.song.valence, new_song.valence])

        self.assertEqual(user_emotion.energy, expected_energy)
        self.assertEqual(user_emotion.valence, expected_valence)

    def test_downvoting_song_does_not_update_user_emotion_attributes(self):
        user_emotion = self.user.useremotion_set.get(emotion__name=Emotion.HAPPY)
        pre_energy = user_emotion.energy
        pre_valence = user_emotion.valence

        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code,
            'vote': False
        }
        self.api_client.post(self.url, data=data, format='json')

        user_emotion.refresh_from_db()

        self.assertEqual(user_emotion.energy, pre_energy)
        self.assertEqual(user_emotion.valence, pre_valence)

    def test_vote_with_context_saves_data_to_vote(self):
        context = 'WORK'
        description = 'Working on moodytunes'

        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code,
            'context': context,
            'description': description,
            'vote': False
        }

        self.api_client.post(self.url, data=data, format='json')
        vote = UserSongVote.objects.get(
            user=self.user,
            emotion__name=Emotion.HAPPY,
            song=self.song
        )

        self.assertEqual(vote.context, context)
        self.assertEqual(vote.description, description)

    def test_vote_with_context_and_blank_description_is_ok(self):
        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code,
            'context': 'WORK',
            'description': '',
            'vote': False
        }

        resp = self.api_client.post(self.url, data=data, format='json')

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_vote_with_empty_context_and_description_is_ok(self):
        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code,
            'context': '',
            'description': 'Working on stuff',
            'vote': False
        }

        resp = self.api_client.post(self.url, data=data, format='json')

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_vote_with_invalid_context_returns_bad_request(self):
        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code,
            'context': 'some-bad-context',
            'vote': False
        }

        resp = self.api_client.post(self.url, data=data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_happy_path(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)

        vote_record = UserSongVote.objects.create(
            user=self.user,
            emotion=emotion,
            song=self.song,
            vote=True
        )

        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code
        }

        resp = self.api_client.delete(self.url, data=data, format='json')
        vote_record.refresh_from_db()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(vote_record.vote)

    def test_delete_does_not_delete_downvote(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)

        UserSongVote.objects.create(
            user=self.user,
            emotion=emotion,
            song=self.song,
            vote=False
        )

        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code
        }

        resp = self.api_client.delete(self.url, data=data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_bad_request_data(self):
        data = {
            'emotion': 'foobarbaz',
            'song_code': self.song.code
        }

        resp = self.api_client.delete(self.url, data=data, format='json')

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_vote_not_found(self):
        data = {
            'emotion': Emotion.HAPPY,
            'song_code': self.song.code
        }

        resp = self.api_client.delete(self.url, data=data, format='json')

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_with_duplicate_votes_for_different_contexts_is_allowed(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)

        # Create a vote for a song with one context
        # (This is the one we'll delete in this test)
        deleted_vote = UserSongVote.objects.create(
            user=self.user,
            emotion=emotion,
            song=self.song,
            context='WORK',
            vote=True
        )

        # Create a vote for the same song with a different context
        # (This is one that should still be upvoted afterwards)
        consistent_vote = UserSongVote.objects.create(
            user=self.user,
            emotion=emotion,
            song=self.song,
            context='PARTY',
            vote=True
        )

        data = {
            'emotion': emotion.name,
            'song_code': self.song.code,
            'context': 'WORK'
        }

        resp = self.api_client.delete(self.url, data=data, format='json')
        deleted_vote.refresh_from_db()
        consistent_vote.refresh_from_db()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(deleted_vote.vote)
        self.assertTrue(consistent_vote.vote)


class TestPlaylistView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.api_client = APIClient()
        cls.url = reverse('tunes:playlist')
        cls.user = MoodyUtil.create_user()
        cls.song = MoodyUtil.create_song()
        cls.emotion = Emotion.objects.get(name=Emotion.HAPPY)

    def setUp(self):
        self.api_client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    def test_unauthenticated_request_is_forbidden(self):
        self.api_client.logout()

        data = {'emotion': self.emotion.name}
        resp = self.api_client.get(self.url, data=data)

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_query_params_passed_returns_bad_request(self):
        resp = self.api_client.get(self.url)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_emotion_returns_bad_request(self):
        data = {'emotion': 'some-bad-value'}
        resp = self.api_client.get(self.url, data=data)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_happy_path(self):
        UserSongVote.objects.create(
            user=self.user,
            song=self.song,
            emotion=self.emotion,
            vote=True
        )

        data = {'emotion': self.emotion.name}
        resp = self.api_client.get(self.url, data=data)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_data['results'][0]['song']['code'], self.song.code)

    def test_downvoted_songs_are_not_returned(self):
        UserSongVote.objects.create(
            user=self.user,
            song=self.song,
            emotion=self.emotion,
            vote=False
        )

        data = {'emotion': self.emotion.name}
        resp = self.api_client.get(self.url, data=data)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_data['results']), 0)

    def test_filter_playlist_by_genre(self):
        new_song = MoodyUtil.create_song(genre='super-dope')
        UserSongVote.objects.create(
            user=self.user,
            song=self.song,
            emotion=self.emotion,
            vote=True
        )
        UserSongVote.objects.create(
            user=self.user,
            song=new_song,
            emotion=self.emotion,
            vote=True
        )

        data = {
            'emotion': self.emotion.name,
            'genre': new_song.genre
        }
        resp = self.api_client.get(self.url, data=data)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_data['results']), 1)
        self.assertEqual(resp_data['results'][0]['song']['code'], new_song.code)

    def test_filter_by_context(self):
        expected_song = MoodyUtil.create_song(name='song-with-context')
        context = 'WORK'

        UserSongVote.objects.create(
            user=self.user,
            song=expected_song,
            emotion=self.emotion,
            vote=True,
            context=context
        )

        UserSongVote.objects.create(
            user=self.user,
            song=self.song,
            emotion=self.emotion,
            vote=True,
        )

        data = {
            'emotion': self.emotion.name,
            'context': context
        }
        resp = self.api_client.get(self.url, data=data)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_data['results']), 1)
        self.assertEqual(resp_data['results'][0]['song']['code'], expected_song.code)

    def test_multiple_votes_for_a_song_does_not_return_duplicate_songs(self):
        # Create two upvotes in different contexts
        UserSongVote.objects.create(
            user=self.user,
            song=self.song,
            emotion=self.emotion,
            vote=True,
            context='WORK'
        )

        UserSongVote.objects.create(
            user=self.user,
            song=self.song,
            emotion=self.emotion,
            vote=True,
            context='PARTY'
        )

        data = {'emotion': self.emotion.name}
        resp = self.api_client.get(self.url, data=data)
        resp_data = resp.json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_data['results']), 1)  # We should only see the song once in the response


class TestOptionsView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('tunes:options')
        cls.user = MoodyUtil.create_user()
        cls.song = MoodyUtil.create_song()
        cls.api_client = APIClient()

    def setUp(self):
        self.api_client.login(username=self.user.username, password=MoodyUtil.DEFAULT_USER_PASSWORD)

    def test_unauthenticated_request_is_forbidden(self):
        self.api_client.logout()

        resp = self.api_client.get(self.url)

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_happy_path(self):
        expected_emotions = [{'name': emotion.full_name, 'code': emotion.name} for emotion in Emotion.objects.all()]
        expected_genres = [self.song.genre]
        expected_contexts = [{'code': choice[0], 'name': choice[1]} for choice in UserSongVote.CONTEXT_CHOICES]

        expected_response = {
            'emotions': expected_emotions,
            'genres': expected_genres,
            'contexts': expected_contexts
        }

        resp = self.api_client.get(self.url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertDictEqual(resp.json(), expected_response)
