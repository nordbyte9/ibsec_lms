from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from assignments.models import CourseAssignment
from courses.models import Course, SecurityCategory, TrainingProgram
from quizzes.models import (
    Answer,
    Option,
    Question,
    Quiz,
    QuizAttempt,
    Submission,
)
from tests.utils import create_user


class QuizAttemptLifecycleTests(TestCase):
    def setUp(self):
        self.employee = create_user(
            'attempt_employee',
            password='password123',
            role='employee',
        )
        self.other_employee = create_user(
            'attempt_other',
            password='password123',
            role='employee',
        )
        self.security_officer = create_user(
            'attempt_security',
            password='password123',
            role='security_officer',
        )
        self.admin = create_user(
            'attempt_admin',
            password='password123',
            role='admin',
        )

        category = SecurityCategory.objects.create(
            code='attempt-lifecycle',
            name='Жизненный цикл попытки',
            description='Проверка серверного таймера',
        )
        program = TrainingProgram.objects.create(
            title='Программа тестирования попыток',
            category=category,
            description='Описание',
            is_mandatory=True,
            periodicity_days=365,
        )
        self.course = Course.objects.create(
            title='Курс с серверным таймером',
            description='Описание',
            training_program=program,
            is_mandatory=True,
            validity_days=365,
            author=self.admin,
            is_published=True,
        )
        self.quiz = Quiz.objects.create(
            course=self.course,
            title='Защищённый тест',
            description='Описание',
            pass_score=50,
            time_limit_minutes=20,
            max_attempts=3,
            is_active=True,
        )
        self.question = Question.objects.create(
            quiz=self.quiz,
            text='Контрольный вопрос',
        )
        self.correct_option = Option.objects.create(
            question=self.question,
            text='Правильный вариант',
            is_correct=True,
        )
        self.wrong_option = Option.objects.create(
            question=self.question,
            text='Неправильный вариант',
            is_correct=False,
        )
        CourseAssignment.objects.create(
            employee=self.employee,
            course=self.course,
            assigned_by=self.security_officer,
            due_date=date(2030, 1, 1),
            status=CourseAssignment.Status.ASSIGNED,
        )
        CourseAssignment.objects.create(
            employee=self.other_employee,
            course=self.course,
            assigned_by=self.security_officer,
            due_date=date(2030, 1, 1),
            status=CourseAssignment.Status.ASSIGNED,
        )

    def _take_url(self):
        return reverse('quizzes:take', args=[self.quiz.pk])

    def _start_attempt(self, user=None):
        self.client.force_login(user or self.employee)
        response = self.client.get(self._take_url())
        self.assertEqual(response.status_code, 200)
        return response.context['attempt']

    def _payload(self, attempt, option=None):
        return {
            'attempt_token': str(attempt.token),
            f'question_{self.question.pk}': str(
                (option or self.correct_option).pk
            ),
        }

    def test_get_creates_in_progress_attempt(self):
        attempt = self._start_attempt()

        self.assertEqual(
            attempt.status,
            QuizAttempt.Status.IN_PROGRESS,
        )
        self.assertEqual(attempt.attempt_number, 1)
        self.assertGreater(attempt.expires_at, attempt.started_at)
        self.assertEqual(Submission.objects.count(), 0)

    def test_refresh_resumes_same_attempt(self):
        first_attempt = self._start_attempt()
        response = self.client.get(self._take_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['attempt'].pk,
            first_attempt.pk,
        )
        self.assertEqual(QuizAttempt.objects.count(), 1)

    def test_post_without_attempt_token_is_rejected(self):
        self.client.force_login(self.employee)
        response = self.client.post(
            self._take_url(),
            {f'question_{self.question.pk}': self.correct_option.pk},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Submission.objects.count(), 0)

    def test_valid_post_completes_attempt_and_creates_submission(self):
        attempt = self._start_attempt()
        response = self.client.post(
            self._take_url(),
            self._payload(attempt),
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Submission.objects.count(), 1)
        self.assertEqual(Answer.objects.count(), 1)

        attempt.refresh_from_db()
        submission = Submission.objects.get()

        self.assertEqual(
            attempt.status,
            QuizAttempt.Status.SUBMITTED,
        )
        self.assertEqual(attempt.submission, submission)
        self.assertIsNotNone(attempt.submitted_at)
        self.assertTrue(submission.passed)
        self.assertEqual(submission.attempt_number, 1)

    def test_repeated_post_does_not_create_second_submission(self):
        attempt = self._start_attempt()
        payload = self._payload(attempt)

        first_response = self.client.post(self._take_url(), payload)
        second_response = self.client.post(self._take_url(), payload)

        self.assertEqual(first_response.status_code, 302)
        self.assertEqual(second_response.status_code, 409)
        self.assertEqual(Submission.objects.count(), 1)
        self.assertEqual(Answer.objects.count(), 1)

    def test_expired_attempt_is_rejected_by_server(self):
        attempt = self._start_attempt()
        attempt.expires_at = timezone.now() - timedelta(seconds=1)
        attempt.save(update_fields=['expires_at'])

        response = self.client.post(
            self._take_url(),
            self._payload(attempt),
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(Submission.objects.count(), 0)

        attempt.refresh_from_db()
        self.assertEqual(
            attempt.status,
            QuizAttempt.Status.EXPIRED,
        )

    def test_expired_attempt_consumes_attempt_limit(self):
        self.quiz.max_attempts = 1
        self.quiz.save(update_fields=['max_attempts'])
        attempt = self._start_attempt()
        attempt.expires_at = timezone.now() - timedelta(seconds=1)
        attempt.save(update_fields=['expires_at'])

        response = self.client.get(self._take_url())

        self.assertEqual(response.status_code, 403)
        attempt.refresh_from_db()
        self.assertEqual(
            attempt.status,
            QuizAttempt.Status.EXPIRED,
        )
        self.assertEqual(QuizAttempt.objects.count(), 1)

    def test_malformed_attempt_token_is_rejected(self):
        self._start_attempt()

        response = self.client.post(
            self._take_url(),
            {
                'attempt_token': 'not-a-uuid',
                f'question_{self.question.pk}': self.correct_option.pk,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Submission.objects.count(), 0)

    def test_other_users_token_is_rejected(self):
        attempt = self._start_attempt(self.other_employee)
        self.client.force_login(self.employee)

        response = self.client.post(
            self._take_url(),
            self._payload(attempt),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Submission.objects.count(), 0)

    def test_next_attempt_number_follows_expired_attempt(self):
        first_attempt = self._start_attempt()
        first_attempt.expires_at = timezone.now() - timedelta(seconds=1)
        first_attempt.save(update_fields=['expires_at'])

        response = self.client.get(self._take_url())

        self.assertEqual(response.status_code, 200)
        second_attempt = response.context['attempt']
        self.assertEqual(second_attempt.attempt_number, 2)
        self.assertEqual(QuizAttempt.objects.count(), 2)

    def test_legacy_submission_still_counts_toward_limit(self):
        self.quiz.max_attempts = 1
        self.quiz.save(update_fields=['max_attempts'])
        Submission.objects.create(
            user=self.employee,
            quiz=self.quiz,
            score=0,
            percent=0.0,
            passed=False,
            attempt_number=1,
        )
        self.client.force_login(self.employee)

        response = self.client.get(self._take_url())

        self.assertEqual(response.status_code, 403)
        self.assertEqual(QuizAttempt.objects.count(), 0)
