from django import forms

from .models import Course, Lesson


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'title',
            'description',
            'training_program',
            'is_mandatory',
            'validity_days',
            'target_departments',
            'target_positions',
            'is_published',
        ]
        widgets = {
            'target_departments': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'target_positions': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'training_program': forms.Select(attrs={'class': 'form-select'}),
        }


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'content', 'type', 'file', 'order']
