import logging
import smtplib

from django.conf import settings
from django.core.management import CommandError
from django.core.mail import send_mail
from django.urls import reverse

from accounts.models import MoodyUser
from base.management.commands import MoodyBaseCommand


class Command(MoodyBaseCommand):
    help = 'Reset a users password to a randomly generated value'

    email_subject = 'Updated Password For Moodytunes'
    email_body = 'You have requested your password for moodytunes be updated. ' \
                 'Your new password is {password}. ' \
                 'Login at {site} to get access to your account'

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
        self.write_to_log_and_output('Successfully updated user {} password'.format(user.username))

        if user.email:
            try:
                body = self.email_body.format(
                    password=new_password,
                    site='{}{}'.format(settings.SITE_URL, reverse('accounts:login'))
                )
                send_mail(self.email_subject, body, settings.SYSTEM_EMAIL_ADDRESS, [user.email])
                self.write_to_log_and_output('Successfully sent updated password to {}'.format(user.email))
            except smtplib.SMTPException as e:
                self.write_to_log_and_output(
                    'Unable to send password reset email to user {}'.format(user.username),
                    output_stream='stderr',
                    log_level=logging.ERROR,
                    extra={'exc': e}
                )
                self.stdout.write('New password: {}'.format(new_password))

        else:
            self.stdout.write('New password: {}'.format(new_password))
