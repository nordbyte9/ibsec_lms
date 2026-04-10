from django.urls import path
from . import views

app_name = 'quizzes'
urlpatterns = [
    path('course/<int:course_id>/', views.course_quiz_entry, name='course_quiz_entry'),
    path('take/<int:quiz_id>/', views.take_quiz, name='take'),
    path('result/<int:submission_id>/', views.quiz_result, name='result'),
]
