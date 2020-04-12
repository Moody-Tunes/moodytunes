from logging import getLogger

from celery.task import task

from accounts.models import MoodyUser, UserEmotion
from tunes.models import Emotion

logger = getLogger(__name__)


@task(bind=True, max_retries=3, default_retry_delay=60*15)
def create_user_emotion_records_for_user(self, user_id):
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
