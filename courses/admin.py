from django.contrib import admin

from .models import Course, Lesson, SecurityCategory, TrainingProgram


@admin.register(SecurityCategory)
class SecurityCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name', 'description')


@admin.register(TrainingProgram)
class TrainingProgramAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_mandatory', 'periodicity_days')
    list_filter = ('category', 'is_mandatory')
    search_fields = ('title', 'description', 'category__name', 'category__code')


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'training_program', 'is_mandatory', 'validity_days', 'author', 'is_published', 'created_at')
    list_filter = ('is_published', 'is_mandatory', 'training_program')
    search_fields = ('title', 'description', 'training_program__title')
    filter_horizontal = ('target_departments', 'target_positions')
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'type')
    list_filter = ('type', 'course')
