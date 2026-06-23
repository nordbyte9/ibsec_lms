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
    fields = ('order', 'title', 'type', 'content', 'file', 'file_active')
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'training_program',
        'is_mandatory',
        'validity_days',
        'author',
        'is_published',
        'created_at',
    )
    list_filter = ('is_published', 'is_mandatory', 'training_program')
    search_fields = ('title', 'description', 'training_program__title')
    filter_horizontal = ('target_departments', 'target_positions')
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'course',
        'order',
        'type',
        'file_active',
        'file_size',
        'file_uploaded_at',
    )
    list_filter = ('type', 'course', 'file_active')
    search_fields = ('title', 'course__title', 'original_filename', 'file_sha256')
    readonly_fields = (
        'original_filename',
        'file_size',
        'file_content_type',
        'file_sha256',
        'file_uploaded_by',
        'file_uploaded_at',
    )
