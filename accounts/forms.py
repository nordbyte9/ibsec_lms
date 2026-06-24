from django import forms

from .models import Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['department', 'position']
        labels = {
            'department': 'Подразделение',
            'position': 'Должность',
        }
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
        }
