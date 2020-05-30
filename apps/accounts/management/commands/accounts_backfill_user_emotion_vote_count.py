from accounts.models import UserEmotion
from base.management.commands import MoodyBaseCommand


class Command(MoodyBaseCommand):
    help = 'Backfill vote_count value for UserEmotion records'

    def handle(self, *args, **options):
        user_emotions = UserEmotion.objects.all()

        self.write_to_log_and_output('Backfilling vote_count for {} UserEmotion records'.format(user_emotions.count()))

        for user_emotion in user_emotions.iterator():
            user_emotion.save()

        self.write_to_log_and_output('Done backfilling vote_count for UserEmotion records')
