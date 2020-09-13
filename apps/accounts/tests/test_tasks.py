from unittest import mock

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.test import TestCase
from spotify_client.exceptions import SpotifyException

from accounts.exceptions import InsufficientSpotifyScopesError
from accounts.models import MoodyUser, SpotifyUserAuth, UserEmotion, UserSongVote
from accounts.signals import create_user_emotion_records, update_user_emotion_attributes
from accounts.tasks import (
    CreateUserEmotionRecordsForUserTask,
    RefreshTopArtistsFromSpotifyTask,
    UpdateTopArtistsFromSpotifyTask,
    UpdateUserEmotionRecordAttributeTask,
)
from libs.tests.helpers import MoodyUtil, SignalDisconnect
from libs.utils import average
from tunes.models import Emotion


class TestCreateUserEmotionTask(TestCase):
    @classmethod
    def setUpTestData(cls):
        dispatch_uid = 'user_post_save_create_useremotion_records'
        with SignalDisconnect(post_save, create_user_emotion_records, settings.AUTH_USER_MODEL, dispatch_uid):
            cls.user = MoodyUtil.create_user(username='test_user')

    def test_happy_path(self):
        CreateUserEmotionRecordsForUserTask().run(self.user.pk)

        self.user.refresh_from_db()

        useremotion_emotion_names = list(self.user.useremotion_set.values_list(
                'emotion__name',
                flat=True
            ).order_by('emotion__name')
        )
        emotion_names = list(Emotion.objects.values_list('name', flat=True).order_by('name'))

        self.assertListEqual(useremotion_emotion_names, emotion_names)

    def test_raises_exception_if_user_not_found(self):
        invalid_user_pk = 10000

        with self.assertRaises(MoodyUser.DoesNotExist):
            CreateUserEmotionRecordsForUserTask().run(invalid_user_pk)


class TestUpdateUserEmotionTask(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.emotion = Emotion.objects.get(name=Emotion.HAPPY)
        cls.song1 = MoodyUtil.create_song(valence=.75, energy=.55)
        cls.song2 = MoodyUtil.create_song(valence=.55, energy=.75)

    def test_happy_path(self):
        dispatch_uid = 'user_song_vote_post_save_update_useremotion_attributes'
        with SignalDisconnect(post_save, update_user_emotion_attributes, UserSongVote, dispatch_uid):
            MoodyUtil.create_user_song_vote(self.user, self.song1, self.emotion, True)
            MoodyUtil.create_user_song_vote(self.user, self.song2, self.emotion, True)

        UpdateUserEmotionRecordAttributeTask().run(self.user.pk, self.emotion.pk)

        user_emotion = self.user.get_user_emotion_record(self.emotion.name)
        user_votes = self.user.usersongvote_set.all()

        expected_attributes = average(user_votes, 'song__valence', 'song__energy', 'song__danceability')
        expected_valence = expected_attributes['song__valence__avg']
        expected_energy = expected_attributes['song__energy__avg']
        expected_danceability = expected_attributes['song__danceability__avg']

        self.assertEqual(user_emotion.valence, expected_valence)
        self.assertEqual(user_emotion.energy, expected_energy)
        self.assertEqual(user_emotion.danceability, expected_danceability)

    def test_task_creates_user_emotion_record_if_it_does_not_exist(self):
        user_emotion = self.user.get_user_emotion_record(self.emotion.name)
        user_emotion.delete()

        UpdateUserEmotionRecordAttributeTask().run(self.user.pk, self.emotion.pk)

        self.assertTrue(UserEmotion.objects.filter(user=self.user, emotion=self.emotion).exists())

    def test_task_raises_exception_if_user_not_found(self):
        invalid_user_id = 10000

        with self.assertRaises(ValidationError):
            UpdateUserEmotionRecordAttributeTask().run(invalid_user_id, self.emotion.id)

    def test_task_raises_exception_if_emotion_not_found(self):
        invalid_emotion_id = 10000

        with self.assertRaises(Emotion.DoesNotExist):
            UpdateUserEmotionRecordAttributeTask().run(self.user.id, invalid_emotion_id)


class TestUpdateTopArtistsFromSpotifyTask(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.auth = MoodyUtil.create_spotify_user_auth(cls.user)

    @mock.patch('spotify_client.SpotifyClient.get_user_top_artists')
    def test_happy_path(self, mock_get_top_artists):
        top_artists = ['Madlib', 'MF DOOM', 'Surf Curse']
        mock_get_top_artists.return_value = top_artists

        UpdateTopArtistsFromSpotifyTask().run(self.auth.id)

        self.auth.spotify_data.refresh_from_db()
        self.assertListEqual(self.auth.spotify_data.top_artists, top_artists)

    @mock.patch('accounts.tasks.UpdateTopArtistsFromSpotifyTask.retry')
    @mock.patch('spotify_client.SpotifyClient.get_user_top_artists')
    def test_spotify_error_on_get_top_artists_causes_task_to_retry(self, mock_get_top_artists, mock_retry):
        mock_get_top_artists.side_effect = SpotifyException

        UpdateTopArtistsFromSpotifyTask().run(self.auth.id)

        mock_retry.assert_called_once()

    def test_get_auth_record_does_not_exists_raises_error(self):
        invalid_auth_id = 99999

        with self.assertRaises(SpotifyUserAuth.DoesNotExist):
            UpdateTopArtistsFromSpotifyTask().run(invalid_auth_id)

    @mock.patch('accounts.tasks.UpdateTopArtistsFromSpotifyTask.retry')
    @mock.patch('accounts.models.SpotifyUserAuth.refresh_access_token')
    @mock.patch('accounts.models.SpotifyUserAuth.should_refresh_access_token')
    def test_get_auth_record_error_on_refresh_access_token_retries(
            self,
            mock_should_refresh_access_token,
            mock_refresh_access_token,
            mock_retry
    ):
        mock_should_refresh_access_token.return_value = True
        mock_refresh_access_token.side_effect = SpotifyException

        UpdateTopArtistsFromSpotifyTask().run(self.auth.id)

        mock_retry.assert_called_once()

    def test_missing_required_scopes_raises_error(self):
        self.auth.scopes = []
        self.auth.save()

        with self.assertRaises(InsufficientSpotifyScopesError):
            UpdateTopArtistsFromSpotifyTask().run(self.auth.id)


class TestRefreshTopArtistsFromSpotifyTask(TestCase):
    @mock.patch('accounts.tasks.UpdateTopArtistsFromSpotifyTask.delay')
    def test_happy_path(self, mock_update_top_artist_task):
        user_1 = MoodyUtil.create_user(username='test1')
        user_2 = MoodyUtil.create_user(username='test2')
        MoodyUtil.create_spotify_user_auth(user_1, spotify_user_id='test_user_1')
        MoodyUtil.create_spotify_user_auth(user_2, spotify_user_id='test_user_2')

        RefreshTopArtistsFromSpotifyTask().run()

        self.assertEqual(mock_update_top_artist_task.call_count, 2)
