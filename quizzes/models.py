import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from courses.models import Course


class Quiz(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='quizzes',
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    pass_score = models.PositiveIntegerField(default=70)
    time_limit_minutes = models.PositiveIntegerField(default=20)
    max_attempts = models.PositiveIntegerField(default=3)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.course.title} — {self.title}'


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions',
    )
    text = models.TextField()

    def __str__(self):
        return self.text[:50]


class Option(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='options',
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text[:50]


class Submission(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submissions',
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='submissions',
    )
    score = models.PositiveIntegerField(default=0)
    percent = models.FloatField(default=0.0)
    passed = models.BooleanField(default=False)
    taken_at = models.DateTimeField(default=timezone.now)
    attempt_number = models.PositiveIntegerField(default=1)


class QuizAttempt(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = 'in_progress', 'В процессе'
        SUBMITTED = 'submitted', 'Завершена'
        EXPIRED = 'expired', 'Время истекло'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts',
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )
    attempt_number = models.PositiveIntegerField(default=1)
    started_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    submitted_at = models.DateTimeField(null=True, blank=True)
    submission = models.OneToOneField(
        Submission,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attempt_record',
    )

    class Meta:
        indexes = [
            models.Index(
                fields=['user', 'quiz', 'status'],
                name='quiz_attempt_lookup_idx',
            ),
        ]
        ordering = ['-started_at', '-id']

    def __str__(self):
        return (
            f'{self.user.username}: {self.quiz.title} '
            f'— попытка {self.attempt_number}'
        )

    @property
    def has_expired(self):
        return timezone.now() >= self.expires_at


class Answer(models.Model):
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='answers',
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(
        Option,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
