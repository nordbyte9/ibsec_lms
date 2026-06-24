from django.contrib.auth.models import User
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Position(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Profile(models.Model):
    class Role(models.TextChoices):
        EMPLOYEE = 'employee', 'Сотрудник'
        SECURITY_OFFICER = 'security_officer', 'Ответственный за ИБ'
        ADMIN = 'admin', 'Администратор'

    ROLE_CHOICES = Role.choices

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profiles',
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profiles',
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to='profiles/avatars/%Y/%m/',
        blank=True,
        null=True,
    )

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'
