from django.contrib import admin

from .models import Answer, Option, Question, Quiz, Submission


class OptionInline(admin.TabularInline):
    model = Option
    extra = 0


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'pass_score', 'time_limit_minutes', 'max_attempts', 'is_active')
    list_filter = ('is_active', 'course')
    search_fields = ('title', 'description')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'text')
    inlines = [OptionInline]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'percent', 'passed', 'attempt_number', 'taken_at')
    list_filter = ('quiz', 'taken_at', 'passed')


admin.site.register(Option)
admin.site.register(Answer)
