from django import forms
from django.contrib.auth.models import User

from courses.models import Course

from .models import CourseAssignment


class CourseAssignmentForm(forms.ModelForm):
    class Meta:
        model = CourseAssignment
        fields = ['employee', 'course', 'due_date']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = User.objects.filter(profile__role='employee').order_by('username')
        self.fields['course'].queryset = Course.objects.filter(is_mandatory=True).order_by('title')
