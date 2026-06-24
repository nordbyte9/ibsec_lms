from datetime import datetime, time, timedelta

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


START_DATE = datetime(2026, 6, 3, 9, 0)
LAST_DATE = datetime(2026, 6, 19, 18, 0)


def aware(value):
    if timezone.is_naive(value):
        return timezone.make_aware(value, timezone.get_current_timezone())
    return value


def moment(index, start_day=0, hour=9):
    day_offset = start_day + (index % 12)
    value = START_DATE + timedelta(days=day_offset)
    value = value.replace(hour=hour + (index % 7), minute=(index * 7) % 60)
    return aware(value)


class Command(BaseCommand):
    help = 'Переносит демонстрационные даты на период с 03.06.2026 по 19.06.2026.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Подтвердить изменение дат демонстрационных записей.',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            raise CommandError('Добавьте параметр --confirm, чтобы изменить демонстрационные даты.')

        changed = 0

        Assignment = apps.get_model('assignments', 'CourseAssignment')
        for index, obj in enumerate(Assignment.objects.order_by('id')):
            assigned = moment(index, start_day=0, hour=9)
            due = (assigned + timedelta(days=8 + index % 4)).date()
            if due > LAST_DATE.date():
                due = LAST_DATE.date()
            completed = None
            if obj.status == 'completed':
                completed = min(assigned + timedelta(days=3), aware(LAST_DATE))
            Assignment.objects.filter(pk=obj.pk).update(
                assigned_at=assigned,
                due_date=due,
                completed_at=completed,
            )
            changed += 1

        Submission = apps.get_model('quizzes', 'Submission')
        for index, obj in enumerate(Submission.objects.order_by('id')):
            Submission.objects.filter(pk=obj.pk).update(taken_at=moment(index, start_day=2, hour=10))
            changed += 1

        QuizAttempt = apps.get_model('quizzes', 'QuizAttempt')
        for index, obj in enumerate(QuizAttempt.objects.order_by('id')):
            started = moment(index, start_day=2, hour=9)
            expires = started + timedelta(minutes=20)
            submitted = started + timedelta(minutes=8) if obj.status == 'submitted' else None
            QuizAttempt.objects.filter(pk=obj.pk).update(
                started_at=started,
                expires_at=expires,
                submitted_at=submitted,
            )
            changed += 1

        AuditLog = apps.get_model('audit', 'AuditLog')
        for index, obj in enumerate(AuditLog.objects.order_by('id')):
            AuditLog.objects.filter(pk=obj.pk).update(created_at=moment(index, start_day=3, hour=8))
            changed += 1

        SyncLog = apps.get_model('integrations', 'IntegrationSyncLog')
        for index, obj in enumerate(SyncLog.objects.order_by('id')):
            started = moment(index, start_day=1, hour=11)
            finished = started + timedelta(minutes=2) if obj.finished_at else None
            SyncLog.objects.filter(pk=obj.pk).update(started_at=started, finished_at=finished)
            changed += 1

        try:
            Article = apps.get_model('knowledge', 'Article')
            for index, obj in enumerate(Article.objects.order_by('id')):
                created = moment(index, start_day=0, hour=10)
                published = created + timedelta(hours=2) if obj.is_published else None
                Article.objects.filter(pk=obj.pk).update(
                    created_at=created,
                    updated_at=created + timedelta(hours=1),
                    published_at=published,
                )
                changed += 1

            Attachment = apps.get_model('knowledge', 'ArticleAttachment')
            for index, obj in enumerate(Attachment.objects.order_by('id')):
                Attachment.objects.filter(pk=obj.pk).update(created_at=moment(index, start_day=1, hour=12))
                changed += 1
        except LookupError:
            pass

        self.stdout.write(self.style.SUCCESS(
            f'Обновлено записей: {changed}. Все демонстрационные даты находятся не позднее 19.06.2026.'
        ))
