from django import forms
from django.contrib.auth.models import User

from .models import Profile


class SignUpForm(forms.ModelForm):
    email = forms.EmailField(label='Электронная почта')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

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
    first_name = forms.CharField(label='Имя', max_length=150, required=False)
    last_name = forms.CharField(label='Фамилия', max_length=150, required=False)
    email = forms.EmailField(label='Электронная почта', required=False)
    remove_avatar = forms.BooleanField(label='Удалить текущий аватар', required=False)

    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'email', 'department', 'position', 'avatar', 'remove_avatar']
        labels = {
            'department': 'Подразделение',
            'position': 'Должность',
            'avatar': 'Фотография профиля',
        }
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'avatar': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png,image/webp',
                'data-avatar-input': '',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
        for field_name in ('first_name', 'last_name', 'email'):
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if not avatar:
            return avatar
        if getattr(avatar, 'size', 0) > 3 * 1024 * 1024:
            raise forms.ValidationError('Размер изображения не должен превышать 3 МБ.')
        content_type = getattr(avatar, 'content_type', '')
        if content_type and content_type not in {'image/jpeg', 'image/png', 'image/webp'}:
            raise forms.ValidationError('Выберите корректный файл изображения.')
        return avatar

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data.get('first_name', '').strip()
        user.last_name = self.cleaned_data.get('last_name', '').strip()
        user.email = self.cleaned_data.get('email', '').strip()

        if self.cleaned_data.get('remove_avatar') and profile.avatar:
            profile.avatar.delete(save=False)
            profile.avatar = None

        if commit:
            user.save(update_fields=['first_name', 'last_name', 'email'])
            profile.save()
        return profile
