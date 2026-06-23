from django import forms
from django.contrib.auth.models import User

from .models import Profile


class SignUpForm(forms.ModelForm):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        labels = {
            'username': 'Имя пользователя',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Электронная почта',
            'password': 'Пароль',
        }


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
