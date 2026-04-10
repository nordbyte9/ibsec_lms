from django import forms
from .models import Quiz, Question, Option

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['course', 'title', 'description', 'pass_score', 'is_active']

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['quiz', 'text']

class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ['question', 'text', 'is_correct']
