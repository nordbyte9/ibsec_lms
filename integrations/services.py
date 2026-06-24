import csv
import io

from django.contrib.auth.models import User
from django.core.management.base import CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import Department, Position, Profile
from .models import IntegrationSyncLog


HEADER_ALIASES = {
    'username': 'username',
    'имя пользователя': 'username',
    'email': 'email',
    'электронная почта': 'email',
    'почта': 'email',
    'first_name': 'first_name',
    'имя': 'first_name',
    'last_name': 'last_name',
    'фамилия': 'last_name',
    'department': 'department',
    'подразделение': 'department',
    'position': 'position',
    'должность': 'position',
    'role': 'role',
    'роль': 'role',
}

ROLE_ALIASES = {
    'employee': Profile.Role.EMPLOYEE,
    'сотрудник': Profile.Role.EMPLOYEE,
    'security_officer': Profile.Role.SECURITY_OFFICER,
    'ответственный за иб': Profile.Role.SECURITY_OFFICER,
    'ответственный за информационную безопасность': Profile.Role.SECURITY_OFFICER,
    'admin': Profile.Role.ADMIN,
    'администратор': Profile.Role.ADMIN,
}

REQUIRED_FIELDS = {'username', 'email', 'first_name', 'last_name', 'department', 'position', 'role'}


def _decode_uploaded_file(uploaded_file):
    raw = uploaded_file.read()
    try:
        return raw.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise CommandError('Файл должен быть сохранён в кодировке UTF-8.') from exc


def import_organization_file(uploaded_file):
    log = IntegrationSyncLog.objects.create(
        source=IntegrationSyncLog.Source.CSV,
        status=IntegrationSyncLog.Status.STARTED,
    )
    created_departments = set()
    created_positions = set()
    processed_users = 0
    created_users = 0
    updated_users = 0

    try:
        text = _decode_uploaded_file(uploaded_file)
        sample = text[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;')
            reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        except csv.Error:
            reader = csv.DictReader(io.StringIO(text), delimiter=';')
        original_headers = reader.fieldnames or []
        normalized_headers = [HEADER_ALIASES.get((header or '').strip().lower()) for header in original_headers]
        missing = REQUIRED_FIELDS.difference(item for item in normalized_headers if item)
        if missing:
            raise CommandError('В файле отсутствуют обязательные столбцы. Скачайте пример и проверьте заголовки.')

        with transaction.atomic():
            for row_number, source_row in enumerate(reader, start=2):
                row = {}
                for original, normalized in zip(original_headers, normalized_headers):
                    if normalized:
                        row[normalized] = (source_row.get(original) or '').strip()

                username = row.get('username', '')
                if not username:
                    raise CommandError(f'Строка {row_number}: не указано имя пользователя.')

                role_raw = row.get('role', '').lower()
                role = ROLE_ALIASES.get(role_raw)
                if role is None:
                    raise CommandError(f'Строка {row_number}: указана неизвестная роль.')

                department = None
                department_name = row.get('department', '')
                if department_name:
                    department, created = Department.objects.get_or_create(name=department_name)
                    if created:
                        created_departments.add(department.pk)

                position = None
                position_name = row.get('position', '')
                if position_name:
                    position, created = Position.objects.get_or_create(name=position_name)
                    if created:
                        created_positions.add(position.pk)

                user, created = User.objects.get_or_create(username=username)
                if created:
                    created_users += 1
                    user.set_unusable_password()
                else:
                    updated_users += 1
                user.email = row.get('email', '')
                user.first_name = row.get('first_name', '')
                user.last_name = row.get('last_name', '')
                user.save()

                profile, _ = Profile.objects.get_or_create(user=user)
                profile.role = role
                profile.department = department
                profile.position = position
                profile.save()
                processed_users += 1

        log.status = IntegrationSyncLog.Status.SUCCESS
        log.imported_departments = len(created_departments)
        log.imported_positions = len(created_positions)
        log.imported_users = processed_users
        log.message = (
            f'Обработано пользователей: {processed_users}; '
            f'создано: {created_users}; обновлено: {updated_users}.'
        )
        log.finished_at = timezone.now()
        log.save()
        return {
            'log': log,
            'processed_users': processed_users,
            'created_users': created_users,
            'updated_users': updated_users,
            'created_departments': len(created_departments),
            'created_positions': len(created_positions),
        }
    except Exception as exc:
        log.status = IntegrationSyncLog.Status.FAILED
        log.message = str(exc)
        log.finished_at = timezone.now()
        log.save(update_fields=['status', 'message', 'finished_at'])
        raise
