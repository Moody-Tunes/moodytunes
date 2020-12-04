import random
from datetime import timedelta
from unittest import mock

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.test import TestCase
from django.utils import timezone
from spotify_client.exceptions import SpotifyException

from accounts.models import MoodyUser, SpotifyUserAuth, SpotifyUserData, UserEmotion, UserSongVote
from accounts.signals import create_user_emotion_records, update_user_emotion_attributes
from libs.tests.helpers import MoodyUtil, SignalDisconnect
from libs.utils import average
from tunes.models import Emotion, Song


class TestUserEmotion(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Disable signal that creates UserEmotion records on user creation
        # so we can create ones during testing
        dispatch_uid = 'user_post_save_create_useremotion_records'
        with SignalDisconnect(post_save, create_user_emotion_records, settings.AUTH_USER_MODEL, dispatch_uid):
            cls.user = MoodyUtil.create_user(username='test_user')

    def test_uniqueness_on_user_emotion_fields(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        UserEmotion.objects.create(user=self.user, emotion=emotion)

        with self.assertRaises(ValidationError):
            UserEmotion.objects.create(user=self.user, emotion=emotion)

    def test_validate_attributes_raises_error_on_invalid_values(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        user_emotion = UserEmotion.objects.create(user=self.user, emotion=emotion)

        with self.assertRaises(ValidationError):
            user_emotion.energy = 12
            user_emotion.valence = 12
            user_emotion.save()

    def test_update_attributes_sets_values_to_average_of_upvoted_songs(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        song = MoodyUtil.create_song(
            energy=round(random.random(), 2),
            valence=round(random.random(), 2),
            danceability=round(random.random(), 2)
        )
        song2 = MoodyUtil.create_song(
            energy=round(random.random(), 2),
            valence=round(random.random(), 2),
            danceability=round(random.random(), 2)
        )
        user_emotion = UserEmotion.objects.create(user=self.user, emotion=emotion)

        # Skip the post_save signal on UserSongVote to delay updating the attributes
        dispatch_uid = 'user_song_vote_post_save_update_useremotion_attributes'
        with SignalDisconnect(post_save, update_user_emotion_attributes, UserSongVote, dispatch_uid):
            UserSongVote.objects.create(
                user=self.user,
                emotion=emotion,
                song=song,
                vote=True
            )

            UserSongVote.objects.create(
                user=self.user,
                emotion=emotion,
                song=song2,
                vote=True
            )

        songs = Song.objects.filter(pk__in=[song.pk, song2.pk])

        expected_attributes = average(songs, 'valence', 'energy', 'danceability')
        expected_valence = expected_attributes['valence__avg']
        expected_energy = expected_attributes['energy__avg']
        expected_danceability = expected_attributes['danceability__avg']

        user_emotion.update_attributes()
        self.assertEqual(user_emotion.energy, expected_energy)
        self.assertEqual(user_emotion.valence, expected_valence)
        self.assertEqual(user_emotion.danceability, expected_danceability)

    def test_update_attributes_sets_values_to_default_if_no_songs_upvoted(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        song = MoodyUtil.create_song(energy=.50, valence=.75, danceability=.45)
        song2 = MoodyUtil.create_song(energy=.60, valence=.85, danceability=.85)
        user_emot = UserEmotion.objects.create(user=self.user, emotion=emotion)

        UserSongVote.objects.create(
            user=self.user,
            emotion=emotion,
            song=song,
            vote=True
        )

        UserSongVote.objects.create(
            user=self.user,
            emotion=emotion,
            song=song2,
            vote=True
        )

        self.user.usersongvote_set.filter(emotion=emotion).update(vote=False)
        default_emotion_energy = emotion.energy
        default_emotion_valence = emotion.valence
        default_emotion_danceability = emotion.danceability

        user_emot.update_attributes()
        self.assertEqual(user_emot.energy, default_emotion_energy)
        self.assertEqual(user_emot.valence, default_emotion_valence)
        self.assertEqual(user_emot.danceability, default_emotion_danceability)


class TestMoodyUser(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUser.objects.create(username='test_user')

    def test_update_information_happy_path(self):
        data = {
            'username': 'new_name',
            'foo': 'bar',  # Invalid value, just to ensure method doesn't blow up
            'email': 'foo@example.com',
        }

        self.user.update_information(data)
        self.user.refresh_from_db()

        self.assertEqual(self.user.username, data['username'])
        self.assertEqual(self.user.email, data['email'])

    def test_update_information_clears_email_field_if_unset(self):
        self.user.email = 'foo@example.com'
        self.user.save()

        data = {
            'username': self.user.username,
            'email': '',
        }

        self.user.update_information(data)
        self.user.refresh_from_db()

        self.assertEqual(self.user.email, '')

    def test_get_user_emotion_with_valid_emotion_returns_user_emotion_object(self):
        user_emot = self.user.get_user_emotion_record(Emotion.HAPPY)

        self.assertIsInstance(user_emot, UserEmotion)

    def test_get_user_emotion_with_invalid_emotion_returns_none(self):
        user_emot = self.user.get_user_emotion_record('bad-emotion')

        self.assertIsNone(user_emot)


class TestSpotifyUserAuth(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()

    def test_should_refresh_access_token_returns_false_for_recently_created_records(self):
        user_auth = MoodyUtil.create_spotify_user_auth(self.user)
        self.assertFalse(user_auth.should_refresh_access_token)

    def test_should_refresh_access_token_returns_false_for_tokens_refreshed_in_boundary(self):
        user_auth = MoodyUtil.create_spotify_user_auth(self.user)
        user_auth.last_refreshed = timezone.now() - timedelta(minutes=30)

        self.assertFalse(user_auth.should_refresh_access_token)

    def test_should_refreshed_access_token_returns_true_for_tokens_refreshed_passed_boundary(self):
        user_auth = MoodyUtil.create_spotify_user_auth(self.user)
        user_auth.last_refreshed = timezone.now() - timedelta(days=7)

        self.assertTrue(user_auth.should_refresh_access_token)

    def test_encrypted_fields_return_values_on_access(self):
        access_token = 'access:token'
        refresh_token = 'refresh_token'
        user_auth = MoodyUtil.create_spotify_user_auth(
            self.user,
            access_token=access_token,
            refresh_token=refresh_token
        )

        self.assertEqual(user_auth.access_token, access_token)
        self.assertEqual(user_auth.refresh_token, refresh_token)

    @mock.patch('spotify_client.SpotifyClient.refresh_access_token')
    def test_refresh_access_token_happy_path(self, mock_refresh_access_token):
        refresh_access_token = 'mock:spotify:access:token'
        mock_refresh_access_token.return_value = refresh_access_token

        access_token = 'access:token'
        refresh_token = 'refresh_token'
        user_auth = MoodyUtil.create_spotify_user_auth(
            self.user,
            access_token=access_token,
            refresh_token=refresh_token
        )

        old_last_refreshed = user_auth.last_refreshed

        user_auth.refresh_access_token()
        user_auth.refresh_from_db()

        self.assertEqual(user_auth.access_token, refresh_access_token)
        self.assertGreater(user_auth.last_refreshed, old_last_refreshed)

    @mock.patch('spotify_client.SpotifyClient.refresh_access_token')
    def test_refresh_access_token_raises_exception(self, mock_refresh_access_token):
        mock_refresh_access_token.side_effect = SpotifyException

        access_token = 'access:token'
        refresh_token = 'refresh_token'
        user_auth = MoodyUtil.create_spotify_user_auth(
            self.user,
            access_token=access_token,
            refresh_token=refresh_token
        )

        with self.assertRaises(SpotifyException):
            user_auth.refresh_access_token()

    def test_get_and_refresh_spotify_user_auth_record_happy_path(self):
        user_auth = MoodyUtil.create_spotify_user_auth(self.user)
        retrieved_user_auth = SpotifyUserAuth.get_and_refresh_spotify_user_auth_record(user_auth.id)

        self.assertEqual(user_auth.pk, retrieved_user_auth.pk)

    @mock.patch('spotify_client.SpotifyClient.refresh_access_token')
    def test_get_and_refresh_spotify_user_auth_record_refreshes_access_token_if_needed(self, mock_refresh_access_token):
        refresh_access_token = 'mock:spotify:access:token'
        mock_refresh_access_token.return_value = refresh_access_token

        user_auth = MoodyUtil.create_spotify_user_auth(self.user)
        user_auth.last_refreshed = timezone.now() - timedelta(days=7)
        user_auth.save()

        SpotifyUserAuth.get_and_refresh_spotify_user_auth_record(user_auth.id)

        mock_refresh_access_token.assert_called_once_with(user_auth.refresh_token)

    def test_get_and_refresh_spotify_user_auth_record_with_missing_record_raises_exception(self):
        invalid_auth_id = 999999

        with self.assertRaises(SpotifyUserAuth.DoesNotExist):
            SpotifyUserAuth.get_and_refresh_spotify_user_auth_record(invalid_auth_id)

    @mock.patch('spotify_client.SpotifyClient.refresh_access_token')
    def test_get_and_refresh_spotify_user_auth_record_raises_spotify_exception(self, mock_refresh_access_token):
        mock_refresh_access_token.side_effect = SpotifyException

        user_auth = MoodyUtil.create_spotify_user_auth(self.user)
        user_auth.last_refreshed = timezone.now() - timedelta(days=7)
        user_auth.save()

        with self.assertRaises(SpotifyException):
            SpotifyUserAuth.get_and_refresh_spotify_user_auth_record(user_auth.id)

    def test_has_scopes_returns_true_for_scope_assigned_to_record(self):
        scope = 'playlist-modify-public'
        user_auth = MoodyUtil.create_spotify_user_auth(self.user)
        user_auth.scopes = [scope]
        user_auth.save()

        self.assertTrue(user_auth.has_scope(scope))

    def test_has_scopes_returns_false_for_scope_not_assigned_to_record(self):
        scope = 'playlist-modify-public'
        desired_scope = 'user-top-read'
        user_auth = MoodyUtil.create_spotify_user_auth(self.user)
        user_auth.scopes = [scope]
        user_auth.save()

        self.assertFalse(user_auth.has_scope(desired_scope))

    def test_spotify_user_data_creation_and_deletion(self):
        # Test SpotifyUserData record is created on auth record creation
        user_auth = MoodyUtil.create_spotify_user_auth(self.user)
        self.assertTrue(SpotifyUserData.objects.filter(spotifyuserauth__user=self.user).exists())

        # Test SpotifyUserData record is delete on auth record deletion
        user_auth.delete()
        self.assertFalse(SpotifyUserData.objects.filter(spotifyuserauth__user=self.user).exists())


class TestUserSongVote(TestCase):
    @classmethod
    def setUpTestData(cls):
        util = MoodyUtil()
        cls.user = util.create_user()
        cls.song = util.create_song()
        cls.emotion = Emotion.objects.get(name=Emotion.HAPPY)

    def test_deleting_vote_updates_attributes_to_average_of_upvotes(self):
        user_emot = self.user.useremotion_set.get(emotion__name=Emotion.HAPPY)
        test_song = MoodyUtil.create_song(valence=.75, energy=.85)
        test_song_2 = MoodyUtil.create_song(valence=.45, energy=.95)
        test_song_3 = MoodyUtil.create_song(valence=.50, energy=.85)

        # Create votes for each song
        MoodyUtil.create_user_song_vote(self.user, test_song, self.emotion, True)
        MoodyUtil.create_user_song_vote(self.user, test_song_2, self.emotion, True)
        MoodyUtil.create_user_song_vote(self.user, test_song_3, self.emotion, False)  # Should not be factored in
        vote_to_delete = MoodyUtil.create_user_song_vote(self.user, self.song, self.emotion, True)

        vote_to_delete.delete()

        upvotes = UserSongVote.objects.filter(user=self.user, vote=True)
        expected_attributes = average(upvotes, 'song__valence', 'song__energy', 'song__danceability')
        expected_valence = expected_attributes['song__valence__avg']
        expected_energy = expected_attributes['song__energy__avg']
        expected_danceability = expected_attributes['song__danceability__avg']

        user_emot.refresh_from_db()

        self.assertEqual(user_emot.energy, expected_energy)
        self.assertEqual(user_emot.valence, expected_valence)
        self.assertEqual(user_emot.danceability, expected_danceability)

    def test_deleting_all_votes_updates_attributes_to_defaults(self):
        user_emot = self.user.useremotion_set.get(emotion__name=Emotion.HAPPY)
        test_song = MoodyUtil.create_song(valence=.75, energy=.85)
        test_song_2 = MoodyUtil.create_song(valence=.45, energy=.95)

        # Create votes for each song
        vote1 = MoodyUtil.create_user_song_vote(self.user, test_song, self.emotion, True)
        vote2 = MoodyUtil.create_user_song_vote(self.user, test_song_2, self.emotion, True)
        vote3 = MoodyUtil.create_user_song_vote(self.user, self.song, self.emotion, True)

        # Deleting all upvotes should reset attributes to emotion defaults
        expected_new_energy = self.emotion.energy
        expected_new_valence = self.emotion.valence

        vote1.delete()
        vote2.delete()
        vote3.delete()

        user_emot.refresh_from_db()

        self.assertEqual(user_emot.energy, expected_new_energy)
        self.assertEqual(user_emot.valence, expected_new_valence)
