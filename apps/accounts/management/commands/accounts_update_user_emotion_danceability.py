from base.management.commands import MoodyBaseCommand

from accounts.models import UserEmotion


class Command(MoodyBaseCommand):
    def handle(self, *args, **options):
        user_emotions = UserEmotion.objects.filter(danceability=0)

        self.write_to_log_and_output('Updating {} user emotion danceability records'.format(user_emotions.count()))

        for user_emotion in user_emotions:
            user_emotion.update_attributes()
