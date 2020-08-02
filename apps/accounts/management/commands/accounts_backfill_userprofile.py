from accounts.models import MoodyUser, UserProfile
from base.management.commands import MoodyBaseCommand


class Command(MoodyBaseCommand):

    def handle(self, *args, **options):
        self.write_to_log_and_output('Starting run to backfill UserProfile records')

        users = MoodyUser.objects.filter(userprofile__isnull=True)

        self.write_to_log_and_output('Creating {} UserProfile records'.format(users.count()))

        for user in users:
            UserProfile.objects.create(user=user)

        self.write_to_log_and_output('Finished run to backfill UserProfile records')
