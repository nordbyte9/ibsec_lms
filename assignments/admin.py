from django.contrib import admin

from .models import CourseAssignment


@admin.register(CourseAssignment)
class CourseAssignmentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'course', 'assigned_by', 'due_date', 'status')
    list_filter = ('status', 'course', 'due_date')
    search_fields = ('employee__username', 'employee__email', 'course__title')
