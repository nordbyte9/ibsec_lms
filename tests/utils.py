from django.contrib.auth.models import User

from accounts.models import Department, Position, Profile


def create_user(username, password='password123', role='employee', department_name=None, position_name=None, **extra):
    user = User.objects.create_user(
        username=username,
        email=extra.get('email', f'{username}@example.com'),
        password=password,
        first_name=extra.get('first_name', ''),
        last_name=extra.get('last_name', ''),
    )
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.role = role
    if department_name:
        department, _ = Department.objects.get_or_create(name=department_name)
        profile.department = department
    if position_name:
        position, _ = Position.objects.get_or_create(name=position_name)
        profile.position = position
    profile.save()
    return user
