from logging import getLogger

from celery.schedules import crontab
from django.conf import settings
from spotify_client import SpotifyClient
from spotify_client.exceptions import SpotifyException

from accounts.exceptions import InsufficientSpotifyScopesError
from accounts.models import MoodyUser, SpotifyUserAuth, UserEmotion
from base.tasks import MoodyBaseTask, MoodyPeriodicTask
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


class UpdateTopArtistsFromSpotifyTask(MoodyBaseTask):
    default_retry_delay = 60 * 15
    autoretry_for = (SpotifyException,)

    @update_logging_data
    def run(self, auth_id, *args, **kwargs):
        auth = SpotifyUserAuth.get_and_refresh_spotify_user_auth_record(auth_id)

        # Check that user has granted proper scopes to fetch top artists from Spotify
        if not auth.has_scope(settings.SPOTIFY_TOP_ARTIST_READ_SCOPE):
            logger.error(
                'User {} has not granted proper scopes to fetch top artists from Spotify'.format(auth.user.username),
                extra={
                    'fingerprint': auto_fingerprint('missing_scopes_for_update_top_artists', **kwargs),
                    'auth_id': auth.pk,
                    'scopes': auth.scopes,
                }
            )

            raise InsufficientSpotifyScopesError('Insufficient Spotify scopes to fetch Spotify top artists')

        spotify_client_identifier = 'update_spotify_top_artists_{}'.format(auth.spotify_user_id)
        spotify = SpotifyClient(identifier=spotify_client_identifier)

        logger.info(
            'Updating top artists for {}'.format(auth.spotify_user_id),
            extra={'fingerprint': auto_fingerprint('update_spotify_top_artists', **kwargs)}
        )

        artists = spotify.get_user_top_artists(auth.access_token, settings.SPOTIFY['max_top_artists'])
        spotify_user_data = auth.spotify_data
        spotify_user_data.top_artists = artists
        spotify_user_data.save()
        logger.info(
            'Successfully updated top artists for {}'.format(auth.spotify_user_id),
            extra={'fingerprint': auto_fingerprint('success_update_spotify_top_artists', **kwargs)}
        )


class RefreshTopArtistsFromSpotifyTask(MoodyPeriodicTask):
    run_every = crontab(minute=0, hour=3, day_of_week=0)

    @update_logging_data
    def run(self, *args, **kwargs):
        auth_records = SpotifyUserAuth.objects.all()

        logger.info(
            'Starting run to refresh top artists for {} auth records'.format(auth_records.count()),
            extra={'fingerprint': auto_fingerprint('refresh_top_artists', **kwargs)}
        )

        for auth in auth_records:
            UpdateTopArtistsFromSpotifyTask().delay(auth.pk)
