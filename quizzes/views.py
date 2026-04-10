from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.http import HttpResponseForbidden
from courses.models import Course
from .models import Quiz, Question, Option, Submission, Answer

@login_required
def course_quiz_entry(request, course_id):
    course = get_object_or_404(Course, pk=course_id, is_published=True)
    quiz = course.quizzes.filter(is_active=True).first()
    return render(request, 'quizzes/quiz_detail.html', {'course': course, 'quiz': quiz})

@login_required
@transaction.atomic
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id, is_active=True)
    questions = quiz.questions.prefetch_related('options').all()
    if request.method == 'POST':
        submission = Submission.objects.create(user=request.user, quiz=quiz, score=0.0)
        correct = 0
        for q in questions:
            selected_id = request.POST.get(f'question_{q.id}')
            selected = Option.objects.filter(pk=selected_id).first() if selected_id else None
            Answer.objects.create(submission=submission, question=q, selected_option=selected)
            if selected and selected.is_correct:
                correct += 1
        total = questions.count() or 1
        score = round(correct / total * 100, 2)
        submission.score = score
        submission.save()
        return redirect('quizzes:result', submission_id=submission.id)
    return render(request, 'quizzes/quiz_take.html', {'quiz': quiz, 'questions': questions})

@login_required
def quiz_result(request, submission_id):
    submission = get_object_or_404(Submission, pk=submission_id, user=request.user)
    return render(request, 'quizzes/quiz_result.html', {'submission': submission})
