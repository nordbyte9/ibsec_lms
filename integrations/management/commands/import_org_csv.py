import csv
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import Department, Position, Profile
from integrations.models import IntegrationSyncLog


class Command(BaseCommand):
    help = 'Import organization structure from CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str)

    def handle(self, *args, **options):
        csv_path = Path(options['csv_path'])
        if not csv_path.exists():
            raise CommandError(f'CSV file not found: {csv_path}')

        log = IntegrationSyncLog.objects.create(
            source=IntegrationSyncLog.Source.CSV,
            status=IntegrationSyncLog.Status.STARTED,
        )

        imported_departments = set()
        imported_positions = set()
        imported_users = 0

        try:
            with transaction.atomic():
                with csv_path.open('r', encoding='utf-8-sig', newline='') as csv_file:
                    sample = csv_file.read(4096)
                    csv_file.seek(0)
                    try:
                        dialect = csv.Sniffer().sniff(sample, delimiters=',;')
                    except csv.Error:
                        dialect = csv.excel
                    reader = csv.DictReader(csv_file, dialect=dialect)
                    required_columns = {'username', 'email', 'first_name', 'last_name', 'department', 'position', 'role'}
                    missing_columns = required_columns.difference(reader.fieldnames or [])
                    if missing_columns:
                        raise CommandError(f'Missing columns: {", ".join(sorted(missing_columns))}')

                    for row_number, row in enumerate(reader, start=2):
                        username = (row.get('username') or '').strip()
                        email = (row.get('email') or '').strip()
                        first_name = (row.get('first_name') or '').strip()
                        last_name = (row.get('last_name') or '').strip()
                        department_name = (row.get('department') or '').strip()
                        position_name = (row.get('position') or '').strip()
                        role = (row.get('role') or '').strip()

                        if not username:
                            raise CommandError(f'Row {row_number}: username is required')
                        if role not in dict(Profile.ROLE_CHOICES):
                            raise CommandError(f'Row {row_number}: invalid role "{role}"')

                        department = None
                        if department_name:
                            department, _ = Department.objects.get_or_create(name=department_name)
                            imported_departments.add(department.pk)

                        position = None
                        if position_name:
                            position, _ = Position.objects.get_or_create(name=position_name)
                            imported_positions.add(position.pk)

                        user, created = User.objects.get_or_create(username=username)
                        user.email = email
                        user.first_name = first_name
                        user.last_name = last_name
                        if created and not user.has_usable_password():
                            user.set_unusable_password()
                        user.save()

                        profile, _ = Profile.objects.get_or_create(user=user)
                        profile.role = role
                        profile.department = department
                        profile.position = position
                        profile.save()
                        imported_users += 1

            log.status = IntegrationSyncLog.Status.SUCCESS
            log.imported_departments = len(imported_departments)
            log.imported_positions = len(imported_positions)
            log.imported_users = imported_users
            log.message = f'Imported from {csv_path.name}'
            log.finished_at = timezone.now()
            log.save(update_fields=[
                'status',
                'imported_departments',
                'imported_positions',
                'imported_users',
                'message',
                'finished_at',
            ])
            self.stdout.write(self.style.SUCCESS('CSV import completed successfully.'))
        except Exception as exc:
            log.status = IntegrationSyncLog.Status.FAILED
            log.message = str(exc)
            log.finished_at = timezone.now()
            log.save(update_fields=['status', 'message', 'finished_at'])
            raise
