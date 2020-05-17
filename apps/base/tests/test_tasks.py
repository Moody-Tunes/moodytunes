import os
from datetime import timedelta

from django.conf import settings
from django.contrib.sessions.models import Session
from django.test import TestCase
from django.utils import timezone

from base.tasks import BackupDatabaseTask, ClearExpiredSessionsTask


class TestClearExpiredSessionsTask(TestCase):
    def test_happy_path(self):
        expired_session_date = timezone.now() - timedelta(seconds=settings.SESSION_COOKIE_AGE + 1)
        Session.objects.create(
            session_data='foobar',
            session_key='bizbaz',
            expire_date=expired_session_date
        )

        ClearExpiredSessionsTask().run()
        self.assertEqual(Session.objects.count(), 0)


class TestBackupDatabaseTask(TestCase):
    def test_happy_path(self):
        BackupDatabaseTask().run()

        for model in settings.DATABASE_BACKUP_TARGETS:
            backup_filename = os.path.join(settings.DATABASE_BACKUPS_PATH, f'{model}.json')
            self.assertTrue(os.path.exists(backup_filename))

    def test_delete_old_backups_clears_files(self):
        with open(os.path.join(settings.DATABASE_BACKUPS_PATH, 'test'), 'w') as test_file:
            test_file.write('Hello World!')

        BackupDatabaseTask().delete_old_backups()

        self.assertFalse(os.listdir(settings.DATABASE_BACKUPS_PATH))
