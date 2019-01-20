from django.core.management import CommandError

from accounts.models import MoodyUser
from base.management.commands import MoodyBaseCommand


class Command(MoodyBaseCommand):
    help = 'Reset a users password to a randomly generated value'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            help='Username of account to reset'
        )

    def handle(self, *args, **options):
        try:
            user = MoodyUser.objects.get(username=options['username'])
        except MoodyUser.DoesNotExist:
            raise CommandError('Could not retrieve user with username {}'.format(options['username']))

        self.write_to_log_and_output('Updating password for user {}'.format(user.username))
        new_password = MoodyUser.objects.make_random_password(length=20)
        user.set_password(new_password)
        user.save()
        self.write_to_log_and_output('Successfully updated user ')

        if user.email:
            # TODO: Send user email of updated password
            pass
        else:
            self.stdout.write('New password: {}'.format(new_password))
