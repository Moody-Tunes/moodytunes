import logging

from django.core.management import CommandError

from accounts.models import SpotifyUserAuth
from base.management.commands import MoodyBaseCommand
from libs.moody_logging import auto_fingerprint, update_logging_data
from libs.tests.helpers import MoodyUtil
from spotify.tasks import UpdateTopArtistsFromSpotifyTask


class Command(MoodyBaseCommand):
    help = 'Management command to copy SpotifyUserAuth records to SpotifyAuth table'

    @update_logging_data
    def handle(self, *args, **options):
        spotify_user_auths = SpotifyUserAuth.objects.all()
        self.write_to_log_and_output(
            'Copying {} SpotifyUserAuth records to SpotifyAuth'.format(spotify_user_auths.count()),
            extra={'fingerprint': auto_fingerprint('start_spotifyauth_create', **options)}
        )

        for spotify_user_auth in spotify_user_auths:
            try:

                # Use the test helper client to skip the `post_save` signal to avoid update Spotify top artists.
                #
                # Need to do this because ordinarily the top artists are updated on SpotifyAuth creation,
                # but there is a chance that the access_token for the SpotifyUserAuth record we are copying
                # could be expired and not valid for use in requests. Combined with the fact that the
                # `last_refreshed` field is auto set when the record is created, we wouldn't know that the
                # access_token should be refreshed and therefore be unable to update the Spotify top artists.
                spotify_auth = MoodyUtil.create_spotify_auth(
                    user=spotify_user_auth.user,
                    spotify_user_id=spotify_user_auth.spotify_user_id,
                    access_token=spotify_user_auth.access_token,
                    refresh_token=spotify_user_auth.refresh_token,
                    scopes=spotify_user_auth.scopes
                )

                spotify_auth.refresh_access_token()  # Manually refresh the access token to ensure validity
                UpdateTopArtistsFromSpotifyTask().delay(spotify_auth.pk)

                self.write_to_log_and_output(
                    'Created SpotifyAuth<{}> from SpotifyUserAuth<{}>'.format(spotify_auth.pk, spotify_user_auth.pk),
                    extra={
                        'spotify_user_id': spotify_auth.spotify_user_id,
                        'moody_user_id': spotify_auth.user.pk,
                        'fingerprint': auto_fingerprint('created_spotifyauth_from_spotifyuserauth', **options)
                    }
                )

            except Exception as exc:
                self.write_to_log_and_output(
                    'Error creating SpotifyAuth record from SpotifyUserAuth<{}>'.format(spotify_user_auth.pk),
                    output_stream='stderr',
                    log_level=logging.ERROR,
                    extra={
                        'exc': exc,
                        'fingerprint': auto_fingerprint('error_creating_spotifyauth_from_spotifyuserauth', **options)
                    }
                )

                raise CommandError(
                    'Error creating SpotifyAuth record from SpotifyUserAuth<{}>.'.format(spotify_user_auth.pk)
                )

        self.write_to_log_and_output(
            'Finished creating {} SpotifyAuth records'.format(spotify_user_auths.count()),
            extra={'fingerprint': auto_fingerprint('finish_spotifyauth_create', **options)}
        )
