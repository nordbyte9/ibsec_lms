from django import forms

from .models import Option, Question, Quiz


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['course', 'title', 'description', 'pass_score', 'time_limit_minutes', 'max_attempts', 'is_active']


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['quiz', 'text']


class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ['question', 'text', 'is_correct']
