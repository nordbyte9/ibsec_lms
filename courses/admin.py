from django.contrib import admin
from .models import Course, Lesson

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'is_published', 'created_at')
    list_filter = ('is_published',)
    search_fields = ('title', 'description')
    inlines = [LessonInline]

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'type')
    list_filter = ('type', 'course')
