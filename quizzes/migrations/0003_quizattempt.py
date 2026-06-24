# Generated for the secure quiz-attempt lifecycle.

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def backfill_quiz_attempts(apps, schema_editor):
    Submission = apps.get_model('quizzes', 'Submission')
    QuizAttempt = apps.get_model('quizzes', 'QuizAttempt')

    for submission in Submission.objects.all().iterator():
        QuizAttempt.objects.get_or_create(
            submission_id=submission.pk,
            defaults={
                'user_id': submission.user_id,
                'quiz_id': submission.quiz_id,
                'token': uuid.uuid4(),
                'status': 'submitted',
                'attempt_number': submission.attempt_number,
                'started_at': submission.taken_at,
                'expires_at': submission.taken_at,
                'submitted_at': submission.taken_at,
            },
        )




class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('quizzes', '0002_quiz_max_attempts_quiz_time_limit_minutes_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuizAttempt',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'token',
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                    ),
                ),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('in_progress', 'В процессе'),
                            ('submitted', 'Завершена'),
                            ('expired', 'Время истекло'),
                        ],
                        default='in_progress',
                        max_length=20,
                    ),
                ),
                (
                    'attempt_number',
                    models.PositiveIntegerField(default=1),
                ),
                (
                    'started_at',
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ('expires_at', models.DateTimeField()),
                (
                    'submitted_at',
                    models.DateTimeField(blank=True, null=True),
                ),
                (
                    'quiz',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='attempts',
                        to='quizzes.quiz',
                    ),
                ),
                (
                    'submission',
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='attempt_record',
                        to='quizzes.submission',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='quiz_attempts',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-started_at', '-id'],
            },
        ),
        migrations.AddIndex(
            model_name='quizattempt',
            index=models.Index(
                fields=['user', 'quiz', 'status'],
                name='quiz_attempt_lookup_idx',
            ),
        ),
        migrations.RunPython(
            backfill_quiz_attempts,
            migrations.RunPython.noop,
        ),
    ]
