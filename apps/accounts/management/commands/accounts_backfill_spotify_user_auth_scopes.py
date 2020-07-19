from django.conf import settings

from accounts.models import SpotifyUserAuth
from base.management.commands import MoodyBaseCommand


class Command(MoodyBaseCommand):

    def handle(self, *args, **options):
        self.write_to_log_and_output('Starting backfill of SpotifyUserAuth scopes')

        for auth in SpotifyUserAuth.objects.iterator():
            auth.scopes = settings.SPOTIFY['auth_user_scopes']
            auth.save()
            self.write_to_log_and_output('Updated scopes for SpotifyUserAuth record: {}'.format(auth.pk))

        self.write_to_log_and_output('Finished backfilling SpotifyUserAuth scopes')
