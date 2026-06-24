from pathlib import Path

from django import forms


class OrganizationImportForm(forms.Form):
    data_file = forms.FileField(
        label='Файл CSV',
        help_text='Формат CSV; разделитель — точка с запятой или запятая; размер — до 2 МБ.',
        widget=forms.ClearableFileInput(attrs={
            'class': 'visually-hidden-file-input',
            'accept': '.csv,text/csv,text/plain',
            'data-import-file': '',
        }),
    )

    def clean_data_file(self):
        uploaded = self.cleaned_data['data_file']
        if uploaded.size > 2 * 1024 * 1024:
            raise forms.ValidationError('Размер файла не должен превышать 2 МБ.')
        if Path(uploaded.name).suffix.lower() != '.csv':
            raise forms.ValidationError('Выберите файл CSV.')
        return uploaded
