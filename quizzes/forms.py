from django import forms

from .models import Option, Question, Quiz


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['course', 'title', 'description', 'pass_score', 'time_limit_minutes', 'max_attempts', 'is_active']
        labels = {
            'course': 'Курс',
            'title': 'Название теста',
            'description': 'Описание',
            'pass_score': 'Проходной балл',
            'time_limit_minutes': 'Лимит времени (минут)',
            'max_attempts': 'Максимум попыток',
            'is_active': 'Активен',
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['quiz', 'text']
        labels = {
            'quiz': 'Тест',
            'text': 'Вопрос',
        }


class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ['question', 'text', 'is_correct']
        labels = {
            'question': 'Вопрос',
            'text': 'Вариант ответа',
            'is_correct': 'Правильный ответ',
        }
