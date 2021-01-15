from logging import getLogger

from django.core.exceptions import ValidationError

from accounts.models import MoodyUser, UserEmotion
from base.tasks import MoodyBaseTask
from libs.moody_logging import auto_fingerprint, update_logging_data
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
    def run(self, user_id, emotion_id, *args, **kwargs):
        """
        Update UserEmotion attributes for a given MoodyUser and Emotion

        :param user_id: (int) Primary key for MoodyUser in our system
        :param emotion_id: (int) Primary key for Emotion in our system

        """
        # We should always call get_or_create to ensure that if we add new emotions, we'll auto
        # create the corresponding UserEmotion record the first time a user votes on a song
        # for the emotion
        try:
            user_emotion, _ = UserEmotion.objects.select_related('emotion', 'user').get_or_create(
                user_id=user_id,
                emotion_id=emotion_id
            )
        except ValidationError as e:
            logger.exception(
                'Unable to create UserEmotion record for user_id={} and emotion_id={}'.format(user_id, emotion_id),
                extra={
                    'fingerprint': auto_fingerprint('failed_to_create_user_emotion', **kwargs),
                    'error': e.error_dict
                }
            )

            raise

        user = user_emotion.user
        emotion = user_emotion.emotion

        old_energy = user_emotion.energy
        old_valence = user_emotion.valence
        old_danceability = user_emotion.danceability

        user_emotion.update_attributes()

        logger.info(
            'Updated UserEmotion attributes for user {} for emotion {}'.format(
                user.username,
                emotion.full_name
            ),
            extra={
                'fingerprint': auto_fingerprint('updated_user_emotion_attributes', **kwargs),
                'user_id': user.id,
                'emotion_id': emotion.id,
                'old_energy': old_energy,
                'old_valence': old_valence,
                'old_danceability': old_danceability,
                'new_energy': user_emotion.energy,
                'new_valence': user_emotion.valence,
                'new_danceability': user_emotion.danceability,
            }
        )
