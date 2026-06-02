from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from assignments.models import CourseAssignment
from courses.models import Course

from .models import Answer, Option, Quiz, Submission


def _can_view_all_results(user):
    return user.is_authenticated and user.profile.role in ('security_officer', 'admin')


def _can_manage_assignments(user):
    return user.is_authenticated and user.profile.role in ('security_officer', 'admin')


def _submission_queryset_for_user(user):
    queryset = Submission.objects.select_related('user', 'quiz', 'quiz__course').order_by('-taken_at')
    if _can_view_all_results(user):
        return queryset
    return queryset.filter(user=user)


def _update_assignment_on_pass(user, quiz):
    assignment = (
        CourseAssignment.objects.filter(employee=user, course=quiz.course)
        .order_by('-assigned_at', '-id')
        .first()
    )
    if assignment:
        assignment.status = CourseAssignment.Status.COMPLETED
        assignment.completed_at = timezone.now()
        assignment.save(update_fields=['status', 'completed_at'])


@login_required
def course_quiz_entry(request, course_id):
    course = get_object_or_404(Course, pk=course_id, is_published=True)
    quiz = course.quizzes.filter(is_active=True).first()
    attempts_used = quiz.submissions.filter(user=request.user).count() if quiz else 0
    return render(
        request,
        'quizzes/quiz_detail.html',
        {
            'course': course,
            'quiz': quiz,
            'attempts_used': attempts_used,
        },
    )


@login_required
@transaction.atomic
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id, is_active=True)
    questions = quiz.questions.prefetch_related('options').all()
    attempts_used = Submission.objects.filter(user=request.user, quiz=quiz).count()
    if attempts_used >= quiz.max_attempts:
        return HttpResponseForbidden('Лимит попыток исчерпан')

    if request.method == 'POST':
        next_attempt = attempts_used + 1
        submission = Submission.objects.create(
            user=request.user,
            quiz=quiz,
            score=0,
            percent=0.0,
            passed=False,
            attempt_number=next_attempt,
        )
        correct = 0
        for q in questions:
            selected_id = request.POST.get(f'question_{q.id}')
            selected = Option.objects.filter(pk=selected_id).first() if selected_id else None
            Answer.objects.create(submission=submission, question=q, selected_option=selected)
            if selected and selected.is_correct:
                correct += 1

        total = questions.count() or 1
        percent = round(correct / total * 100, 2)
        submission.score = correct
        submission.percent = percent
        submission.passed = percent >= quiz.pass_score
        submission.save(update_fields=['score', 'percent', 'passed'])

        if submission.passed:
            _update_assignment_on_pass(request.user, quiz)

        return redirect('quizzes:result', submission_id=submission.id)

    return render(
        request,
        'quizzes/quiz_take.html',
        {
            'quiz': quiz,
            'questions': questions,
            'attempts_used': attempts_used,
            'attempts_left': max(quiz.max_attempts - attempts_used, 0),
        },
    )


@login_required
def quiz_result(request, submission_id):
    submission = get_object_or_404(Submission.objects.select_related('user', 'quiz', 'quiz__course'), pk=submission_id)
    if submission.user != request.user and not _can_view_all_results(request.user):
        return HttpResponseForbidden('Недостаточно прав')
    return render(request, 'quizzes/quiz_result.html', {'submission': submission})


@login_required
def attempt_history(request):
    submissions = _submission_queryset_for_user(request.user)
    return render(request, 'quizzes/attempt_history.html', {'submissions': submissions})
