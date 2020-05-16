from logging import getLogger

from celery.schedules import crontab

from accounts.models import MoodyUser, SpotifyUserAuth, UserEmotion, UserSongVote
from base.tasks import MoodyBaseTask, MoodyPeriodicTask
from libs.moody_logging import auto_fingerprint, update_logging_data
from libs.spotify import SpotifyClient, SpotifyException
from tunes.models import Emotion


logger = getLogger(__name__)


class CreateUserEmotionRecordsForUserTask(MoodyBaseTask):

    @update_logging_data
    def run(self, user_id, *args, **kwargs):
        """
        Create UserEmotion records for a user for each emotion we have in our system

        :param user_id: (int) Primary key for user record
        """
        try:
            user = MoodyUser.objects.get(pk=user_id)
        except (MoodyUser.DoesNotExist, MoodyUser.MultipleObjectsReturned):
            logger.exception(
                'Unable to fetch MoodyUser with pk={}'.format(user_id),
                extra={'fingerprint': auto_fingerprint('failed_to_fetch_user', **kwargs)}
            )
            raise

        user_emotions = []
        for emotion in Emotion.objects.all().iterator():
            user_emotions.append(
                UserEmotion(
                    user=user,
                    emotion=emotion,
                    energy=emotion.energy,
                    valence=emotion.valence,
                    danceability=emotion.danceability,
                )
            )

        UserEmotion.objects.bulk_create(user_emotions)

        logger.info(
            'Created UserEmotion records for user {}'.format(user.username),
            extra={'fingerprint': auto_fingerprint('created_user_emotion_records', **kwargs)}
        )


class UpdateUserEmotionRecordAttributeTask(MoodyBaseTask):

    @update_logging_data
    def run(self, vote_id, *args, **kwargs):
        """
        Update UserEmotion attributes for an upvoted song

        :param vote_id: (int) Primary key for vote record

        """
        try:
            vote = UserSongVote.objects.select_related('user', 'emotion', 'song').get(pk=vote_id)
        except (UserSongVote.DoesNotExist, UserSongVote.MultipleObjectsReturned):
            logger.exception(
                'Unable to fetch UserSongVote with pk={}'.format(vote_id),
                extra={'fingerprint': auto_fingerprint('failed_to_fetch_vote', **kwargs)}
            )
            raise

        # We should always call get_or_create to ensure that if we add new emotions, we'll auto
        # create the corresponding UserEmotion record the first time a user votes on a song
        # for the emotion
        user_emotion, _ = vote.user.useremotion_set.get_or_create(
            emotion__name=vote.emotion.name,
            defaults={
                'user': vote.user,
                'emotion': vote.emotion
            }
        )

        old_energy = user_emotion.energy
        old_valence = user_emotion.valence
        old_danceability = user_emotion.danceability

        user_emotion.update_attributes()

        logger.info(
            'Updated UserEmotion attributes for user {} for emotion {}'.format(
                vote.user.username,
                vote.emotion.full_name
            ),
            extra={
                'fingerprint': auto_fingerprint('updated_user_emotion_attributes', **kwargs),
                'user_id': vote.user.id,
                'emotion_id': vote.emotion.id,
                'song_id': vote.song.id,
                'old_energy': old_energy,
                'old_valence': old_valence,
                'old_danceability': old_danceability,
                'new_energy': user_emotion.energy,
                'new_valence': user_emotion.valence,
                'new_danceability': user_emotion.danceability,
                'song_energy': vote.song.energy,
                'song_valence': vote.song.valence,
                'song_danceability': vote.song.danceability,
            }
        )


class SpotifyAuthUserTaskMixin(object):

    def retry(self):
        """Dummy method for calling celery retry for task. Needed for testing purposes."""
        return super(SpotifyAuthUserTaskMixin, self).retry()

    @update_logging_data
    def get_and_refresh_spotify_user_auth_record(self, auth_id, **kwargs):
        """
        Fetch the SpotifyUserAuth record for the given primary key, and refresh if
        the access token is expired

        :param auth_id: (int) Primary key for SpotifyUserAuth record

        :return: (SpotifyUserAuth)
        """
        try:
            auth = SpotifyUserAuth.objects.get(pk=auth_id)
        except (SpotifyUserAuth.MultipleObjectsReturned, SpotifyUserAuth.DoesNotExist):
            logger.error(
                'Failed to fetch SpotifyUserAuth with pk={}'.format(auth_id),
                extra={'fingerprint': auto_fingerprint('failed_to_fetch_spotify_user_auth', **kwargs)},
            )

            raise

        if auth.should_update_access_token:
            try:
                auth.refresh_access_token()
            except SpotifyException:
                logger.warning(
                    'Failed to update access token for SpotifyUserAuth with pk={}'.format(auth_id),
                    extra={'fingerprint': auto_fingerprint('failed_to_update_access_token', **kwargs)},
                )
                self.retry()

        return auth


class CreateSpotifyAuthUserSavedTracksTask(MoodyBaseTask, SpotifyAuthUserTaskMixin):
    max_retries = 3
    default_retry_delay = 60 * 15

    @update_logging_data
    def run(self, user_auth_id, *args, **kwargs):
        """
        Fetch the songs the user has saved in their Spotify account and save to their
        record for use in generating their browse playlist.

        :param user_auth_id: (int) Primary key of SpotifyAuthUser record to fetch
        """
        auth = self.get_and_refresh_spotify_user_auth_record(user_auth_id)
        client = SpotifyClient(identifier='create_spotify_saved_tracks:{}'.format(auth.spotify_user_id))

        try:
            spotify_track_ids = client.get_user_saved_tracks(auth.access_token)
            auth.saved_songs = spotify_track_ids
            auth.save()
            logger.info(
                'Successfully updated Spotify saved songs for user {}'.format(auth.spotify_user_id),
                extra={
                    'fingerprint': auto_fingerprint('success_get_saved_songs_from_spotify', **kwargs),
                    'spotify_user_id': auth.spotify_user_id,
                    'spotify_user_auth_id': auth.pk
                }
            )
        except SpotifyException:
            logger.warning(
                'Error fetching user saved songs from Spotify for user {}'.format(auth.spotify_user_id),
                extra={
                    'fingerprint': auto_fingerprint('failed_get_saved_songs_from_spotify', **kwargs),
                    'spotify_user_id': auth.spotify_user_id,
                    'spotify_user_auth_id': auth.pk
                }
            )

            self.retry()


class UpdateSpotifyAuthUserSavedTracksTask(MoodyPeriodicTask):
    run_every = crontab(minute=0, hour=2, day_of_week=0)

    @update_logging_data
    def run(self, *args, **kwargs):
        """
        Periodically update the saved_songs for each of the SpotifyUserAuth records we have stored.
        This will ensure we keep our concept of user saved tracks on Spotify fresh.
        """
        auths = SpotifyUserAuth.objects.all()

        for auth in auths:
            logger.info(
                'Updating user saved tracks from Spotify',
                extra={
                    'fingerprint': auto_fingerprint('update_saved_tracks_from_spotify', **kwargs),
                    'auth_id': auth.pk
                }
            )
            CreateSpotifyAuthUserSavedTracksTask().delay(auth.pk)
