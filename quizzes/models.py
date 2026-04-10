from django.db import models
from django.contrib.auth.models import User
from courses.models import Course
from django.utils import timezone

class Quiz(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    pass_score = models.PositiveIntegerField(default=70)  # %
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.course.title} — {self.title}'

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()

    def __str__(self):
        return self.text[:50]

class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text[:50]

class Submission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='submissions')
    score = models.FloatField(default=0.0)  # в процентах
    taken_at = models.DateTimeField(default=timezone.now)

    def passed(self):
        return self.score >= self.quiz.pass_score

class Answer(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.SET_NULL, null=True, blank=True)
