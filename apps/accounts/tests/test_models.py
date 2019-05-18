from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.test import TestCase

from accounts.models import MoodyUser, UserEmotion, UserSongVote
from accounts.signals import create_user_emotion_records, update_user_boundaries
from tunes.models import Emotion
from libs.tests.helpers import SignalDisconnect, MoodyUtil
from libs.utils import average


class TestUserEmotion(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Disable signal that creates UserEmotion records on user creation
        # so we can create ones during testing
        dispatch_uid = 'user_post_save_create_useremotion_records'
        with SignalDisconnect(post_save, create_user_emotion_records,
                              settings.AUTH_USER_MODEL, dispatch_uid):
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
        dispatch_uid = 'user_song_vote_post_save_update_useremotion_boundaries'
        with SignalDisconnect(post_save, update_user_boundaries,
                              UserSongVote, dispatch_uid):
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
    def test_update_information(self):
        user = MoodyUser.objects.create(username='test_user')
        data = {
            'username': 'new_name',
            'email': 'foo@example.com',
            'foo': 'bar'  # Invalid value, just to ensure method doesn't blow up
        }

        user.update_information(data)
        user.refresh_from_db()

        self.assertEqual(user.username, data['username'])
        self.assertEqual(user.email, data['email'])


class TestUserSongVote(TestCase):
    @classmethod
    def setUpTestData(cls):
        util = MoodyUtil()
        cls.user = util.create_user()
        cls.song = util.create_song()
        cls.emotion = Emotion.objects.get(name=Emotion.HAPPY)

    def test_deleting_vote_updates_attributes(self):
        user_emot = self.user.useremotion_set.get(emotion__name=Emotion.HAPPY)

        expected_new_energy = user_emot.energy
        expected_new_valence = user_emot.valence

        vote = UserSongVote.objects.create(
            user=self.user,
            emotion=self.emotion,
            song=self.song,
            vote=True
        )

        vote.delete()

        user_emot.refresh_from_db()

        self.assertEqual(user_emot.energy, expected_new_energy)
        self.assertEqual(user_emot.valence, expected_new_valence)
