import uuid
from pathlib import Path

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from accounts.models import Department, Position

from .file_security import inspect_uploaded_file, validate_protected_upload


def protected_lesson_upload_to(instance, filename):
    """Сохраняет новое вложение под случайным именем."""

    extension = Path(filename).suffix.lower()
    return f'protected/lessons/{uuid.uuid4().hex}{extension}'


class SecurityCategory(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class TrainingProgram(models.Model):
    title = models.CharField(max_length=255)
    category = models.ForeignKey(
        SecurityCategory,
        on_delete=models.PROTECT,
        related_name='programs',
    )
    description = models.TextField(blank=True)
    is_mandatory = models.BooleanField(default=False)
    periodicity_days = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    training_program = models.ForeignKey(
        TrainingProgram,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
    )
    is_mandatory = models.BooleanField(default=False)
    validity_days = models.PositiveIntegerField(null=True, blank=True)
    target_departments = models.ManyToManyField(
        Department,
        blank=True,
        related_name='target_courses',
    )
    target_positions = models.ManyToManyField(
        Position,
        blank=True,
        related_name='target_courses',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='authored_courses',
    )
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Lesson(models.Model):
    TYPE_CHOICES = [
        ('text', 'Текст'),
        ('link', 'Ссылка'),
        ('file', 'Файл'),
    ]

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons',
    )
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='text')
    file = models.FileField(
        upload_to=protected_lesson_upload_to,
        validators=[validate_protected_upload],
        blank=True,
        null=True,
    )
    original_filename = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveBigIntegerField(null=True, blank=True)
    file_content_type = models.CharField(max_length=127, blank=True)
    file_sha256 = models.CharField(max_length=64, blank=True, db_index=True)
    file_uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_lesson_files',
    )
    file_uploaded_at = models.DateTimeField(null=True, blank=True)
    file_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']

    def save(self, *args, **kwargs):
        if self.file and not getattr(self.file, '_committed', True):
            inspection = inspect_uploaded_file(self.file)
            self.original_filename = inspection.original_name
            self.file_size = inspection.size
            self.file_content_type = inspection.content_type
            self.file_sha256 = inspection.sha256
            self.file_uploaded_at = timezone.now()
            self.file_active = True

        super().save(*args, **kwargs)

    @property
    def download_filename(self):
        if self.original_filename:
            return self.original_filename
        if self.file:
            return Path(self.file.name).name
        return 'material'

    def __str__(self):
        return f'{self.course.title} — {self.title}'
