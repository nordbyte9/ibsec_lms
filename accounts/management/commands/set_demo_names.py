from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


DEMO_NAMES = {
    'admin': ('Системный', 'администратор'),
    'security_officer': ('Ответственный', 'за ИБ'),
    'employee': ('Сотрудник', '№ 1'),
    'employee2': ('Сотрудник', '№ 2'),
}


class Command(BaseCommand):
    help = (
        'Заполняет русские отображаемые имена демонстрационных '
        'пользователей IBSec LMS.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Перезаписать уже заполненные имя и фамилию.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать изменения без сохранения в базе данных.',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        force = options['force']
        dry_run = options['dry_run']

        updated = 0
        skipped = 0
        missing = 0

        for username, (first_name, last_name) in DEMO_NAMES.items():
            user = User.objects.filter(username=username).first()

            if user is None:
                missing += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'Пользователь {username!r} не найден — пропущен.'
                    )
                )
                continue

            has_existing_name = bool(
                user.first_name.strip() or user.last_name.strip()
            )

            if has_existing_name and not force:
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'{username}: имя уже заполнено '
                        f'({user.get_full_name() or username}) — пропущен. '
                        'Для перезаписи используйте --force.'
                    )
                )
                continue

            full_name = f'{first_name} {last_name}'.strip()

            if dry_run:
                self.stdout.write(
                    f'[ПРОВЕРКА] {username} → {full_name}'
                )
                updated += 1
                continue

            user.first_name = first_name
            user.last_name = last_name
            user.save(update_fields=['first_name', 'last_name'])
            updated += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'{username} → {full_name}'
                )
            )

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Проверка завершена: планируется обновить {updated}, '
                    f'пропущено {skipped}, не найдено {missing}.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Готово: обновлено {updated}, '
                    f'пропущено {skipped}, не найдено {missing}.'
                )
            )
