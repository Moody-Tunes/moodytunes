from base.management.commands import MoodyBaseCommand


class Command(MoodyBaseCommand):

    def handle(self, *args, **options):
        self.stdout.write('Hello World!')
