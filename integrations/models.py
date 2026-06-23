from django.db import models


class IntegrationSyncLog(models.Model):
    class Source(models.TextChoices):
        CSV = 'csv', 'CSV'

    class Status(models.TextChoices):
        STARTED = 'started', 'Запущено'
        SUCCESS = 'success', 'Успешно'
        FAILED = 'failed', 'Ошибка'

    source = models.CharField(max_length=32, choices=Source.choices)
    status = models.CharField(max_length=32, choices=Status.choices)
    imported_departments = models.PositiveIntegerField(default=0)
    imported_positions = models.PositiveIntegerField(default=0)
    imported_users = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at', '-id']

    def __str__(self):
        return f'{self.source} / {self.status} / {self.started_at:%Y-%m-%d %H:%M}'
