from django_celery_beat.models import PeriodicTask

from base.management.commands import MoodyBaseCommand


class Command(MoodyBaseCommand):
    def handle(self, *args, **options):
        self.logger.info('Disabling all registered PeriodicTasks')
        PeriodicTask.objects.all().update(enabled=False)
