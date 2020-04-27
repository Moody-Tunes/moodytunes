from logging import getLogger

from accounts.models import MoodyUser, UserEmotion, UserSongVote
from base.tasks import MoodyBaseTask
from tunes.models import Emotion

logger = getLogger(__name__)


class CreateUserEmotionRecordsForUserTask(MoodyBaseTask):

    def run(self, user_id, *args, **kwargs):
        """
        Create UserEmotion records for a user for each emotion we have in our system

        :param user_id: (int) Primary key for user record
        """
        try:
            user = MoodyUser.objects.get(pk=user_id)
        except (MoodyUser.DoesNotExist, MoodyUser.MultipleObjectsReturned):
            logger.exception('Unable to fetch MoodyUser with pk={}'.format(user_id))
            raise

        logger.info('Creating UserEmotion records for user {}'.format(user.username))

        for emotion in Emotion.objects.all().iterator():
            UserEmotion.objects.create(
                user=user,
                emotion=emotion
            )

        logger.info('Created UserEmotion records for user {}'.format(user.username))


class UpdateUserEmotionRecordAttributeTask(MoodyBaseTask):

    def run(self, vote_id, *args, **kwargs):
        """
        Update UserEmotion attributes for an upvoted song

        :param vote_id: (int) Primary key for vote record

        """
        try:
            vote = UserSongVote.objects.get(pk=vote_id)
        except (UserSongVote.DoesNotExist, UserSongVote.MultipleObjectsReturned):
            logger.exception('Unable to fetch UserSongVote with pk={}'.format(vote_id))
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

        logger.info('Updating UserEmotion attributes for user {} for emotion {}'.format(
            vote.user.username,
            vote.emotion.full_name
        ))

        user_emotion.update_attributes()
        user_emotion.refresh_from_db()

        logger.info('Updated UserEmotion attributes for user {} for emotion {}'.format(
                vote.user.username,
                vote.emotion.full_name
            ),
            extra={
                'old_energy': old_energy,
                'old_valence': old_valence,
                'old_danceability': old_danceability,
                'new_energy': user_emotion.energy,
                'new_valence': user_emotion.valence,
                'new_danceability': user_emotion.danceability
            }
        )
