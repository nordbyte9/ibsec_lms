from django.contrib.auth.models import User
from django.db import models

from accounts.models import Department, Position


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
    category = models.ForeignKey(SecurityCategory, on_delete=models.PROTECT, related_name='programs')
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
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='authored_courses')
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
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='text')
    file = models.FileField(upload_to='lessons/', blank=True, null=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.course.title} — {self.title}'
