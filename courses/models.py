from django.db import models
from django.contrib.auth.models import User

class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
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
