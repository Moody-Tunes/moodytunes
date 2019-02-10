from django_celery_beat.models import PeriodicTask

from django.core.management import call_command
from django.test import TestCase


class TestDisablePeriodicTasksCommand(TestCase):
    def test_happy_path(self):
        task = PeriodicTask.objects.create(name='test-task', task='test.tasks.test_task')
        call_command('base_disable_periodic_tasks')

        task.refresh_from_db()
        self.assertFalse(task.enabled)
