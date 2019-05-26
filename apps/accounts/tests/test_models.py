from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.utils import timezone
from django.test import TestCase

from accounts.models import MoodyUser, SpotifyUserAuth, UserEmotion, UserSongVote
from accounts.signals import create_user_emotion_records, update_user_attributes
from tunes.models import Emotion
from libs.tests.helpers import SignalDisconnect, MoodyUtil
from libs.utils import average


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
        song = MoodyUtil.create_song(energy=.50, valence=.75)
        song2 = MoodyUtil.create_song(energy=.60, valence=.85)
        user_emot = UserEmotion.objects.create(user=self.user, emotion=emotion)

        # Skip the post_save signal on UserSongVote to delay updating the attributes
        dispatch_uid = 'user_song_vote_post_save_update_useremotion_attributes'
        with SignalDisconnect(post_save, update_user_attributes, UserSongVote, dispatch_uid):
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

        expected_new_energy = average([song.energy, song2.energy])
        expected_new_valence = average([song.valence, song2.valence])

        user_emot.update_attributes()
        self.assertEqual(user_emot.energy, expected_new_energy)
        self.assertEqual(user_emot.valence, expected_new_valence)

    def test_update_attributes_sets_values_to_default_if_no_songs_upvoted(self):
        emotion = Emotion.objects.get(name=Emotion.HAPPY)
        song = MoodyUtil.create_song(energy=.50, valence=.75)
        song2 = MoodyUtil.create_song(energy=.60, valence=.85)
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
        expected_new_energy = emotion.energy
        expected_new_valence = emotion.valence

        user_emot.update_attributes()
        self.assertEqual(user_emot.energy, expected_new_energy)
        self.assertEqual(user_emot.valence, expected_new_valence)


class TestMoodyUser(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MoodyUser.objects.create(username='test_user')

    def test_update_information(self):
        data = {
            'username': 'new_name',
            'foo': 'bar',  # Invalid value, just to ensure method doesn't blow up
            'email': 'foo@example.com',
        }

        self.user.update_information(data)
        self.user.refresh_from_db()

        self.assertEqual(self.user.username, data['username'])
        self.assertEqual(self.user.email, data['email'])

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

    def test_should_updated_access_token_returns_false_for_recently_created_records(self):
        user_auth = SpotifyUserAuth.objects.create(user=self.user, spotify_user_id='test_user')
        self.assertFalse(user_auth.should_updated_access_token)

    def test_should_update_access_token_returns_false_for_tokens_refreshed_in_boundary(self):
        user_auth = SpotifyUserAuth.objects.create(user=self.user, spotify_user_id='test_user')
        user_auth.last_refreshed = timezone.now() - timedelta(minutes=30)

        self.assertFalse(user_auth.should_updated_access_token)

    def test_should_update_access_token_returns_true_for_tokens_refreshed_passed_boundary(self):
        user_auth = SpotifyUserAuth.objects.create(user=self.user, spotify_user_id='test_user')
        user_auth.last_refreshed = timezone.now() - timedelta(days=7)

        self.assertTrue(user_auth.should_updated_access_token)


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

        expected_new_energy = average([test_song.energy, test_song_2.energy])
        expected_new_valence = average([test_song.valence, test_song_2.valence])

        vote_to_delete.delete()

        user_emot.refresh_from_db()

        self.assertEqual(user_emot.energy, expected_new_energy)
        self.assertEqual(user_emot.valence, expected_new_valence)

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
