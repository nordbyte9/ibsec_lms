from datetime import timedelta
import uuid

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Max
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.permissions import Permission, has_permission
from assignments.models import CourseAssignment
from audit.services import log_action
from courses.models import Course

from .models import Answer, Quiz, QuizAttempt, Submission


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

    return has_permission(
        user,
        Permission.TAKE_ASSIGNED_QUIZ,
    ) and _has_course_assignment(user, quiz.course)


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
    """Проверяет, что каждый option_id принадлежит своему вопросу."""

    question_keys = {
        f'question_{question.pk}'
        for question in questions
    }
    submitted_question_keys = {
        key
        for key in request.POST.keys()
        if key.startswith('question_')
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


def _legacy_submissions(user, quiz):
    """Возвращает старые результаты, не связанные с QuizAttempt."""

    return Submission.objects.filter(
        user=user,
        quiz=quiz,
        attempt_record__isnull=True,
    )


def _attempts_used(user, quiz):
    return (
        QuizAttempt.objects.filter(user=user, quiz=quiz).count()
        + _legacy_submissions(user, quiz).count()
    )


def _next_attempt_number(user, quiz):
    tracked_max = (
        QuizAttempt.objects.filter(user=user, quiz=quiz)
        .aggregate(value=Max('attempt_number'))['value']
        or 0
    )
    legacy_max = (
        _legacy_submissions(user, quiz)
        .aggregate(value=Max('attempt_number'))['value']
        or 0
    )
    return max(tracked_max, legacy_max) + 1


def _expire_stale_attempts(request, quiz):
    now = timezone.now()
    stale_attempts = list(
        QuizAttempt.objects.select_for_update().filter(
            user=request.user,
            quiz=quiz,
            status=QuizAttempt.Status.IN_PROGRESS,
            expires_at__lte=now,
        )
    )

    for attempt in stale_attempts:
        attempt.status = QuizAttempt.Status.EXPIRED
        attempt.submitted_at = now
        attempt.save(update_fields=['status', 'submitted_at'])

        log_action(
            request.user,
            'quiz_attempt_expired',
            'QuizAttempt',
            attempt.pk,
            (
                f'Истекло время попытки {attempt.attempt_number} '
                f'теста "{quiz.title}"'
            ),
            request=request,
        )


def _get_or_start_attempt(request, quiz):
    """Возобновляет активную попытку либо безопасно создаёт новую."""

    User.objects.select_for_update().get(pk=request.user.pk)
    _expire_stale_attempts(request, quiz)

    active_attempt = (
        QuizAttempt.objects.select_for_update()
        .filter(
            user=request.user,
            quiz=quiz,
            status=QuizAttempt.Status.IN_PROGRESS,
            expires_at__gt=timezone.now(),
        )
        .order_by('started_at', 'id')
        .first()
    )

    if active_attempt:
        return active_attempt, False

    if _attempts_used(request.user, quiz) >= quiz.max_attempts:
        return None, False

    started_at = timezone.now()
    attempt = QuizAttempt.objects.create(
        user=request.user,
        quiz=quiz,
        status=QuizAttempt.Status.IN_PROGRESS,
        attempt_number=_next_attempt_number(request.user, quiz),
        started_at=started_at,
        expires_at=started_at + timedelta(minutes=quiz.time_limit_minutes),
    )

    log_action(
        request.user,
        'quiz_attempt_started',
        'QuizAttempt',
        attempt.pk,
        (
            f'Начата попытка {attempt.attempt_number} '
            f'теста "{quiz.title}"'
        ),
        request=request,
    )

    return attempt, True


@login_required
def course_quiz_entry(request, course_id):
    course = get_object_or_404(
        Course,
        pk=course_id,
        is_published=True,
    )
    quiz = course.quizzes.filter(is_active=True).first()

    if quiz and not _can_take_quiz(request.user, quiz):
        return HttpResponseForbidden(
            'Тест доступен только по назначенному курсу'
        )

    attempts_used = _attempts_used(request.user, quiz) if quiz else 0
    active_attempt = None

    if quiz:
        active_attempt = QuizAttempt.objects.filter(
            user=request.user,
            quiz=quiz,
            status=QuizAttempt.Status.IN_PROGRESS,
            expires_at__gt=timezone.now(),
        ).first()

    return render(
        request,
        'quizzes/quiz_detail.html',
        {
            'course': course,
            'quiz': quiz,
            'attempts_used': attempts_used,
            'attempts_left': (
                max(quiz.max_attempts - attempts_used, 0)
                if quiz
                else 0
            ),
            'active_attempt': active_attempt,
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
        return HttpResponseForbidden(
            'Тест доступен только по назначенному курсу'
        )

    questions = list(
        quiz.questions.prefetch_related('options').all()
    )

    if request.method == 'POST':
        attempt_token = request.POST.get('attempt_token')

        if not attempt_token:
            _log_invalid_quiz_submission(request, quiz)
            return HttpResponseBadRequest('Не указан идентификатор попытки')

        try:
            attempt_uuid = uuid.UUID(str(attempt_token))
        except (TypeError, ValueError, AttributeError):
            _log_invalid_quiz_submission(request, quiz)
            return HttpResponseBadRequest(
                'Некорректный идентификатор попытки'
            )

        selected_options = _validate_submitted_answers(
            request,
            questions,
        )

        if selected_options is None:
            _log_invalid_quiz_submission(request, quiz)
            return HttpResponseBadRequest('Некорректные данные ответа')

        with transaction.atomic():
            User.objects.select_for_update().get(pk=request.user.pk)

            attempt = (
                QuizAttempt.objects.select_for_update()
                .filter(
                    token=attempt_uuid,
                    user=request.user,
                    quiz=quiz,
                )
                .first()
            )

            if attempt is None:
                _log_invalid_quiz_submission(request, quiz)
                return HttpResponseBadRequest(
                    'Некорректный идентификатор попытки'
                )

            if attempt.status != QuizAttempt.Status.IN_PROGRESS:
                return HttpResponse(
                    'Эта попытка уже завершена',
                    status=409,
                )

            now = timezone.now()

            if now >= attempt.expires_at:
                attempt.status = QuizAttempt.Status.EXPIRED
                attempt.submitted_at = now
                attempt.save(update_fields=['status', 'submitted_at'])

                log_action(
                    request.user,
                    'quiz_attempt_expired',
                    'QuizAttempt',
                    attempt.pk,
                    (
                        f'Истекло время попытки '
                        f'{attempt.attempt_number} теста "{quiz.title}"'
                    ),
                    request=request,
                )

                return HttpResponse(
                    'Время прохождения теста истекло',
                    status=409,
                )

            correct = 0
            answers = []

            for question in questions:
                selected = selected_options[question.pk]

                if selected is not None and selected.is_correct:
                    correct += 1

                answers.append(
                    Answer(
                        question=question,
                        selected_option=selected,
                    )
                )

            total = len(questions) or 1
            percent = round(correct / total * 100, 2)

            submission = Submission.objects.create(
                user=request.user,
                quiz=quiz,
                score=correct,
                percent=percent,
                passed=percent >= quiz.pass_score,
                attempt_number=attempt.attempt_number,
                taken_at=now,
            )

            for answer in answers:
                answer.submission = submission

            Answer.objects.bulk_create(answers)

            attempt.status = QuizAttempt.Status.SUBMITTED
            attempt.submitted_at = now
            attempt.submission = submission
            attempt.save(
                update_fields=[
                    'status',
                    'submitted_at',
                    'submission',
                ]
            )

            log_action(
                request.user,
                'quiz_submitted',
                'Submission',
                submission.pk,
                (
                    f'Сдан тест "{quiz.title}" по курсу '
                    f'"{quiz.course.title}" со счетом '
                    f'{submission.score}/{total} '
                    f'({submission.percent}%)'
                ),
                request=request,
            )

            if submission.passed:
                assignment = _update_assignment_on_pass(
                    request.user,
                    quiz,
                )

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

        return redirect(
            'quizzes:result',
            submission_id=submission.id,
        )

    with transaction.atomic():
        attempt, _created = _get_or_start_attempt(request, quiz)

    if attempt is None:
        return HttpResponseForbidden('Лимит попыток исчерпан')

    attempts_used = _attempts_used(request.user, quiz)
    remaining_seconds = max(
        0,
        int((attempt.expires_at - timezone.now()).total_seconds()),
    )

    return render(
        request,
        'quizzes/quiz_take.html',
        {
            'quiz': quiz,
            'questions': questions,
            'attempt': attempt,
            'attempts_used': attempts_used,
            'attempts_left': max(
                quiz.max_attempts - attempts_used,
                0,
            ),
            'remaining_seconds': remaining_seconds,
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

    if (
        submission.user != request.user
        and not _can_view_all_results(request.user)
    ):
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
