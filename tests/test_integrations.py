import csv
import tempfile
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from accounts.models import Department, Position, Profile
from integrations.models import IntegrationSyncLog


class IntegrationImportTests(TestCase):
    def test_import_org_csv_command(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / 'org.csv'
            with csv_path.open('w', encoding='utf-8-sig', newline='') as csv_file:
                writer = csv.DictWriter(
                    csv_file,
                    fieldnames=['username', 'email', 'first_name', 'last_name', 'department', 'position', 'role'],
                    delimiter=';',
                )
                writer.writeheader()
                writer.writerow(
                    {
                        'username': 'employee_csv',
                        'email': 'employee_csv@example.com',
                        'first_name': 'Иван',
                        'last_name': 'Петров',
                        'department': 'ИТ-отдел',
                        'position': 'Системный администратор',
                        'role': 'employee',
                    }
                )

            call_command('import_org_csv', str(csv_path))

        user = User.objects.get(username='employee_csv')
        profile = Profile.objects.get(user=user)
        self.assertEqual(user.email, 'employee_csv@example.com')
        self.assertEqual(user.first_name, 'Иван')
        self.assertEqual(user.last_name, 'Петров')
        self.assertEqual(profile.role, 'employee')
        self.assertEqual(profile.department, Department.objects.get(name='ИТ-отдел'))
        self.assertEqual(profile.position, Position.objects.get(name='Системный администратор'))

        sync_log = IntegrationSyncLog.objects.get()
        self.assertEqual(sync_log.source, IntegrationSyncLog.Source.CSV)
        self.assertEqual(sync_log.status, IntegrationSyncLog.Status.SUCCESS)
        self.assertEqual(sync_log.imported_departments, 1)
        self.assertEqual(sync_log.imported_positions, 1)
        self.assertEqual(sync_log.imported_users, 1)
