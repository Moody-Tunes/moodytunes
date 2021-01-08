import random
from datetime import timedelta
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from spotify_client.exceptions import SpotifyException

from accounts.models import MoodyUser, SpotifyUserAuth, SpotifyUserData, UserEmotion, UserSongVote
from libs.tests.helpers import MoodyUtil
from libs.utils import average
from tunes.models import Emotion, Song


class TestUserEmotion(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUtil.create_user()
        cls.emotion = Emotion.objects.get(name=Emotion.HAPPY)

    def test_uniqueness_on_user_and_emotion(self):
        self.user.useremotion_set.all().delete()

        # Create a new UserEmotion record for our user and emotion
        UserEmotion.objects.create(user=self.user, emotion=self.emotion)

        # Ensure that a call to create a new UserEmotion record
        # for our user and emotion is invalid
        with self.assertRaises(ValidationError):
            UserEmotion.objects.create(user=self.user, emotion=self.emotion)

    def test_validate_attributes_raises_error_on_invalid_values(self):
        user_emotion = self.user.get_user_emotion_record(self.emotion.name)

        # Attributes should be floats, integers should be invalid values for updates
        user_emotion.energy = 12
        user_emotion.valence = 12

        with self.assertRaises(ValidationError):
            user_emotion.save()

    def test_update_attributes_sets_values_to_average_of_most_recently_upvoted_songs(self):
        user_emotion = self.user.get_user_emotion_record(self.emotion.name)
        candidate_batch_size = 5
        votes = []

        for _ in range(10):
            song = MoodyUtil.create_song(
                energy=round(random.random(), 2),
                valence=round(random.random(), 2),
                danceability=round(random.random(), 2)
            )

            vote = UserSongVote(
                user=self.user,
                emotion=self.emotion,
                song=song,
                vote=True
            )

            votes.append(vote)

        # Use `bulk_create` to make UserSongVote records to skip the signal to update
        # UserEmotion attributes on UserSongVote creation, so we can manually call it
        # during the test to ensure it behaves appropriately
        UserSongVote.objects.bulk_create(votes)

        # Get the songs for the most recent upvotes for the emotion by the user
        # These should be the songs used to calculate the new UserEmotion attributes
        songs = Song.objects.filter(
            pk__in=UserSongVote.objects.filter(
                user=self.user,
                emotion=self.emotion,
                vote=True
            ).order_by(
                '-created'
            ).values_list(
                'song__pk',
                flat=True
            )[:candidate_batch_size]
        )

        expected_attributes = average(songs, 'valence', 'energy', 'danceability')
        expected_valence = expected_attributes['valence__avg']
        expected_energy = expected_attributes['energy__avg']
        expected_danceability = expected_attributes['danceability__avg']

        user_emotion.update_attributes(candidate_batch_size=candidate_batch_size)
        self.assertEqual(user_emotion.energy, expected_energy)
        self.assertEqual(user_emotion.valence, expected_valence)
        self.assertEqual(user_emotion.danceability, expected_danceability)

    def test_update_attributes_sets_values_to_emotion_defaults_if_no_songs_upvoted_for_emotion(self):
        song = MoodyUtil.create_song(energy=.50, valence=.75, danceability=.45)
        song2 = MoodyUtil.create_song(energy=.60, valence=.85, danceability=.85)
        user_emotion = self.user.get_user_emotion_record(self.emotion.name)

        MoodyUtil.create_user_song_vote(
            user=self.user,
            emotion=self.emotion,
            song=song,
            vote=True
        )

        MoodyUtil.create_user_song_vote(
            user=self.user,
            emotion=self.emotion,
            song=song2,
            vote=True
        )

        # Update the votes to set the vote value to False
        self.user.usersongvote_set.filter(emotion=self.emotion).update(vote=False)

        # Call update_attributes directly, because the update call skips the post_save signal
        user_emotion.update_attributes()

        self.assertEqual(user_emotion.energy, self.emotion.energy)
        self.assertEqual(user_emotion.valence, self.emotion.valence)
        self.assertEqual(user_emotion.danceability, self.emotion.danceability)


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
        user_emotion = self.user.get_user_emotion_record(Emotion.HAPPY)

        self.assertIsInstance(user_emotion, UserEmotion)

    def test_get_user_emotion_with_invalid_emotion_returns_none(self):
        user_emotion = self.user.get_user_emotion_record('bad-emotion')

        self.assertIsNone(user_emotion)


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
        user_emotion = self.user.useremotion_set.get(emotion__name=Emotion.HAPPY)
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

        user_emotion.refresh_from_db()

        self.assertEqual(user_emotion.energy, expected_energy)
        self.assertEqual(user_emotion.valence, expected_valence)
        self.assertEqual(user_emotion.danceability, expected_danceability)

    def test_deleting_all_votes_updates_attributes_to_defaults(self):
        user_emotion = self.user.useremotion_set.get(emotion__name=Emotion.HAPPY)
        test_song = MoodyUtil.create_song(valence=.75, energy=.85)
        test_song_2 = MoodyUtil.create_song(valence=.45, energy=.95)

        # Create votes for each song
        vote1 = MoodyUtil.create_user_song_vote(self.user, test_song, self.emotion, True)
        vote2 = MoodyUtil.create_user_song_vote(self.user, test_song_2, self.emotion, True)
        vote3 = MoodyUtil.create_user_song_vote(self.user, self.song, self.emotion, True)

        # Deleting all upvotes should reset attributes to emotion defaults
        expected_new_energy = self.emotion.energy
        expected_new_valence = self.emotion.valence
        expected_new_danceability = self.emotion.danceability

        vote1.delete()
        vote2.delete()
        vote3.delete()

        user_emotion.refresh_from_db()

        self.assertEqual(user_emotion.energy, expected_new_energy)
        self.assertEqual(user_emotion.valence, expected_new_valence)
        self.assertEqual(user_emotion.danceability, expected_new_danceability)
