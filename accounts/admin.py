from django.contrib import admin

from .models import Department, Position, Profile


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'department', 'position')
    list_filter = ('role', 'department', 'position')
    search_fields = (
        'user__username',
        'user__email',
        'department__name',
        'position__name',
    )
