from logging import getLogger

from celery.task import task

from accounts.models import MoodyUser, UserEmotion, UserSongVote
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

@task(bind=True, max_retries=3, default_retry_delay=60*15)
def update_user_emotion_record_attributes(self, vote_id):
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

    logger.info('Updating UserEmotion attributes for user {} for emotion'.format(
        vote.user.username,
        vote.emotion.full_name
    ))

    user_emotion.update_attributes()
