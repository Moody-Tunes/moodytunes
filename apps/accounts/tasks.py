from logging import getLogger

from accounts.models import MoodyUser, SpotifyUserAuth, UserEmotion, UserSongVote
from base.tasks import MoodyBaseTask
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


class UpdateTopArtistsFromSpotifyTask(MoodyBaseTask):
    max_retries = 3
    default_retry_delay = 60 * 15

    @update_logging_data
    def run(self, auth_id, *args, **kwargs):
        try:
            auth = SpotifyUserAuth.get_and_refresh_spotify_user_auth_record(auth_id)
        except SpotifyException:
            return self.retry()

        spotify_client_identifier = 'update_spotify_top_artists_{}'.format(auth.spotify_user_id)
        spotify = SpotifyClient(identifier=spotify_client_identifier)

        logger.info(
            'Updating top artists for {}'.format(auth.spotify_user_id),
            extra={'fingerprint': auto_fingerprint('update_spotify_top_artists', **kwargs)}
        )

        try:
            artists = spotify.get_user_top_artists(auth.access_token)
            auth.top_artists = artists
            auth.save()
            logger.info(
                'Successfully updated top artists for {}'.format(auth.spotify_user_id),
                extra={'fingerprint': auto_fingerprint('success_update_spotify_top_artists', **kwargs)}
            )
        except SpotifyException:
            logger.exception(
                'Error fetching top artists for {}'.format(auth.spotify_user_id),
                extra={
                    'spotify_client_identifier': spotify_client_identifier,
                    'auth_id': auth.pk,
                    'fingerprint': auto_fingerprint('failed_update_spotify_top_artists', **kwargs)
                }
            )

            self.retry()
