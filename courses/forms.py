from django import forms

from .file_security import ALLOWED_EXTENSIONS, DEFAULT_MAX_FILE_SIZE
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
        labels = {
            'title': 'Название курса',
            'description': 'Описание',
            'training_program': 'Программа обучения',
            'is_mandatory': 'Обязательный курс',
            'validity_days': 'Срок действия (дней)',
            'target_departments': 'Целевые подразделения',
            'target_positions': 'Целевые должности',
            'is_published': 'Опубликован',
        }
        widgets = {
            'target_departments': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'target_positions': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'training_program': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'validity_days': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'content', 'type', 'file', 'order']
        labels = {
            'title': 'Название урока',
            'content': 'Содержание',
            'type': 'Тип',
            'file': 'Защищённый файл',
            'order': 'Порядок',
        }
        help_texts = {
            'file': (
                'Разрешены PDF, DOCX, XLSX, PPTX, TXT, CSV, JPG и PNG. '
                f'Максимальный размер по умолчанию — '
                f'{DEFAULT_MAX_FILE_SIZE // (1024 * 1024)} МБ.'
            ),
        }
        widgets = {
            'file': forms.ClearableFileInput(
                attrs={'accept': ','.join(ALLOWED_EXTENSIONS)}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        lesson_type = cleaned_data.get('type')
        uploaded_file = cleaned_data.get('file')

        if lesson_type == 'file' and not uploaded_file:
            self.add_error('file', 'Для урока типа «Файл» необходимо загрузить файл.')

        if lesson_type != 'file' and uploaded_file:
            self.add_error(
                'file',
                'Загрузка файла разрешена только для урока типа «Файл».',
            )

        return cleaned_data
