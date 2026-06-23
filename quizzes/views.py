from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.permissions import Permission, has_permission
from assignments.models import CourseAssignment
from audit.services import log_action
from courses.models import Course

from .models import Answer, Quiz, Submission


def _can_view_all_results(user):
    return has_permission(user, Permission.VIEW_ALL_RESULTS)


def _can_preview_quiz(user):
    """Разрешает служебный просмотр теста ответственному за ИБ и администратору."""

    return has_permission(user, Permission.MANAGE_COURSES)


def _has_course_assignment(user, course):
    """Проверяет наличие назначения курса текущему сотруднику."""

    return CourseAssignment.objects.filter(
        employee=user,
        course=course,
    ).exists()


def _can_take_quiz(user, quiz):
    """Проверяет прикладное и объектное право на прохождение теста."""

    if _can_preview_quiz(user):
        return True

    return has_permission(user, Permission.TAKE_ASSIGNED_QUIZ) and _has_course_assignment(
        user,
        quiz.course,
    )


def _submission_queryset_for_user(user):
    queryset = Submission.objects.select_related(
        'user',
        'quiz',
        'quiz__course',
    ).order_by('-taken_at')

    if _can_view_all_results(user):
        return queryset

    return queryset.filter(user=user)


def _update_assignment_on_pass(user, quiz):
    assignment = (
        CourseAssignment.objects.filter(
            employee=user,
            course=quiz.course,
        )
        .order_by('-assigned_at', '-id')
        .first()
    )

    if assignment:
        assignment.status = CourseAssignment.Status.COMPLETED
        assignment.completed_at = timezone.now()
        assignment.save(update_fields=['status', 'completed_at'])

    return assignment


def _validate_submitted_answers(request, questions):
    """Проверяет, что каждый option_id принадлежит своему вопросу.

    Возвращает словарь ``question_id -> Option | None``. Любое неизвестное
    поле вопроса, повторяющееся значение или вариант из другого вопроса
    считается некорректным запросом.
    """

    question_keys = {f'question_{question.pk}' for question in questions}
    submitted_question_keys = {
        key for key in request.POST.keys() if key.startswith('question_')
    }

    if not submitted_question_keys.issubset(question_keys):
        return None

    selected_options = {}

    for question in questions:
        field_name = f'question_{question.pk}'
        values = request.POST.getlist(field_name)

        if len(values) > 1:
            return None

        selected_id = values[0] if values else ''

        if selected_id in ('', None):
            selected_options[question.pk] = None
            continue

        try:
            selected_pk = int(selected_id)
        except (TypeError, ValueError):
            return None

        # Вариант ищется только среди вариантов текущего вопроса.
        selected = next(
            (
                option
                for option in question.options.all()
                if option.pk == selected_pk
            ),
            None,
        )

        if selected is None:
            return None

        selected_options[question.pk] = selected

    return selected_options


def _log_invalid_quiz_submission(request, quiz):
    log_action(
        request.user,
        'quiz_invalid_submission',
        'Quiz',
        quiz.pk,
        (
            f'Отклонена некорректная отправка теста "{quiz.title}" '
            f'по курсу "{quiz.course.title}"'
        ),
        request=request,
    )


@login_required
def course_quiz_entry(request, course_id):
    course = get_object_or_404(Course, pk=course_id, is_published=True)
    quiz = course.quizzes.filter(is_active=True).first()

    if quiz and not _can_take_quiz(request.user, quiz):
        return HttpResponseForbidden('Тест доступен только по назначенному курсу')

    attempts_used = (
        quiz.submissions.filter(user=request.user).count()
        if quiz
        else 0
    )

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
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(
        Quiz.objects.select_related('course'),
        pk=quiz_id,
        is_active=True,
    )

    if not quiz.course.is_published:
        return HttpResponseForbidden('Курс не опубликован')

    if not _can_take_quiz(request.user, quiz):
        return HttpResponseForbidden('Тест доступен только по назначенному курсу')

    questions = list(
        quiz.questions.prefetch_related('options').all()
    )

    attempts_used = Submission.objects.filter(
        user=request.user,
        quiz=quiz,
    ).count()

    if attempts_used >= quiz.max_attempts:
        return HttpResponseForbidden('Лимит попыток исчерпан')

    if request.method == 'POST':
        selected_options = _validate_submitted_answers(request, questions)

        if selected_options is None:
            _log_invalid_quiz_submission(request, quiz)
            return HttpResponseBadRequest('Некорректные данные ответа')

        with transaction.atomic():
            # Блокировка пользователя сериализует отправки одного пользователя
            # и не позволяет параллельным запросам превысить лимит попыток.
            User.objects.select_for_update().get(pk=request.user.pk)

            attempts_used = Submission.objects.filter(
                user=request.user,
                quiz=quiz,
            ).count()

            if attempts_used >= quiz.max_attempts:
                return HttpResponseForbidden('Лимит попыток исчерпан')

            submission = Submission.objects.create(
                user=request.user,
                quiz=quiz,
                score=0,
                percent=0.0,
                passed=False,
                attempt_number=attempts_used + 1,
            )

            correct = 0
            answers = []

            for question in questions:
                selected = selected_options[question.pk]
                answers.append(
                    Answer(
                        submission=submission,
                        question=question,
                        selected_option=selected,
                    )
                )

                if selected is not None and selected.is_correct:
                    correct += 1

            Answer.objects.bulk_create(answers)

            total = len(questions) or 1
            percent = round(correct / total * 100, 2)

            submission.score = correct
            submission.percent = percent
            submission.passed = percent >= quiz.pass_score
            submission.save(update_fields=['score', 'percent', 'passed'])

            log_action(
                request.user,
                'quiz_submitted',
                'Submission',
                submission.pk,
                (
                    f'Сдан тест "{quiz.title}" по курсу "{quiz.course.title}" '
                    f'со счетом {submission.score}/{total} '
                    f'({submission.percent}%)'
                ),
                request=request,
            )

            if submission.passed:
                assignment = _update_assignment_on_pass(request.user, quiz)

                if assignment:
                    log_action(
                        request.user,
                        'assignment_completed',
                        'CourseAssignment',
                        assignment.pk,
                        (
                            f'Завершено назначение курса '
                            f'"{assignment.course.title}" для пользователя '
                            f'{request.user.get_full_name() or request.user.username}'
                        ),
                        request=request,
                    )

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
    submission = get_object_or_404(
        Submission.objects.select_related(
            'user',
            'quiz',
            'quiz__course',
        ),
        pk=submission_id,
    )

    if submission.user != request.user and not _can_view_all_results(request.user):
        return HttpResponseForbidden('Недостаточно прав')

    return render(
        request,
        'quizzes/quiz_result.html',
        {'submission': submission},
    )


@login_required
def attempt_history(request):
    submissions = _submission_queryset_for_user(request.user)
    return render(
        request,
        'quizzes/attempt_history.html',
        {'submissions': submissions},
    )
