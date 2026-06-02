from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from courses.models import Course


class CourseAssignment(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = 'assigned', 'Назначено'
        IN_PROGRESS = 'in_progress', 'В процессе'
        COMPLETED = 'completed', 'Завершено'
        OVERDUE = 'overdue', 'Просрочено'

    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_assignments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    assigned_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='assigned_courses')
    assigned_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ASSIGNED)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-assigned_at', '-id']

    def __str__(self):
        return f'{self.employee.username} - {self.course.title}'

    def save(self, *args, **kwargs):
        if self.status == self.Status.COMPLETED:
            if self.completed_at is None:
                self.completed_at = timezone.now()
        else:
            self.completed_at = None
        super().save(*args, **kwargs)
