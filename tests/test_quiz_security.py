from datetime import date

from django.test import TestCase
from django.urls import reverse

from assignments.models import CourseAssignment
from audit.models import AuditLog
from courses.models import Course, SecurityCategory, TrainingProgram
from quizzes.models import Answer, Option, Question, Quiz, Submission
from tests.utils import create_user


class QuizSecurityTests(TestCase):
    def setUp(self):
        self.employee = create_user(
            'quiz_employee',
            password='password123',
            role='employee',
        )
        self.unassigned_employee = create_user(
            'quiz_unassigned',
            password='password123',
            role='employee',
        )
        self.security_officer = create_user(
            'quiz_security',
            password='password123',
            role='security_officer',
        )
        self.admin = create_user(
            'quiz_admin',
            password='password123',
            role='admin',
        )

        category = SecurityCategory.objects.create(
            code='quiz-security',
            name='Безопасность тестирования',
            description='Проверка защиты тестов',
        )
        program = TrainingProgram.objects.create(
            title='Программа безопасного тестирования',
            category=category,
            description='Описание',
            is_mandatory=True,
            periodicity_days=365,
        )
        self.course = Course.objects.create(
            title='Курс с защищённым тестом',
            description='Описание',
            training_program=program,
            is_mandatory=True,
            validity_days=365,
            author=self.admin,
            is_published=True,
        )
        self.quiz = Quiz.objects.create(
            course=self.course,
            title='Итоговый тест',
            description='Описание',
            pass_score=50,
            time_limit_minutes=20,
            max_attempts=3,
            is_active=True,
        )

        self.question_one = Question.objects.create(
            quiz=self.quiz,
            text='Первый вопрос',
        )
        self.question_one_correct = Option.objects.create(
            question=self.question_one,
            text='Правильный ответ 1',
            is_correct=True,
        )
        self.question_one_wrong = Option.objects.create(
            question=self.question_one,
            text='Неправильный ответ 1',
            is_correct=False,
        )

        self.question_two = Question.objects.create(
            quiz=self.quiz,
            text='Второй вопрос',
        )
        self.question_two_correct = Option.objects.create(
            question=self.question_two,
            text='Правильный ответ 2',
            is_correct=True,
        )
        self.question_two_wrong = Option.objects.create(
            question=self.question_two,
            text='Неправильный ответ 2',
            is_correct=False,
        )

        self.assignment = CourseAssignment.objects.create(
            employee=self.employee,
            course=self.course,
            assigned_by=self.security_officer,
            due_date=date(2030, 1, 1),
            status=CourseAssignment.Status.ASSIGNED,
        )

        self.other_course = Course.objects.create(
            title='Другой курс',
            description='Описание',
            training_program=program,
            author=self.admin,
            is_published=True,
        )
        self.other_quiz = Quiz.objects.create(
            course=self.other_course,
            title='Другой тест',
            pass_score=70,
            max_attempts=3,
            is_active=True,
        )
        self.other_question = Question.objects.create(
            quiz=self.other_quiz,
            text='Вопрос другого теста',
        )
        self.other_option = Option.objects.create(
            question=self.other_question,
            text='Ответ другого теста',
            is_correct=True,
        )

    def _take_url(self):
        return reverse('quizzes:take', args=[self.quiz.pk])

    def _entry_url(self):
        return reverse('quizzes:course_quiz_entry', args=[self.course.pk])

    def _valid_payload(self):
        return {
            f'question_{self.question_one.pk}': str(
                self.question_one_correct.pk
            ),
            f'question_{self.question_two.pk}': str(
                self.question_two_correct.pk
            ),
        }

    def test_assigned_employee_can_open_quiz(self):
        self.client.force_login(self.employee)

        response = self.client.get(self._take_url())

        self.assertEqual(response.status_code, 200)

    def test_unassigned_employee_cannot_open_course_quiz_entry(self):
        self.client.force_login(self.unassigned_employee)

        response = self.client.get(self._entry_url())

        self.assertEqual(response.status_code, 403)

    def test_unassigned_employee_cannot_open_quiz(self):
        self.client.force_login(self.unassigned_employee)

        response = self.client.get(self._take_url())

        self.assertEqual(response.status_code, 403)

    def test_security_officer_can_preview_quiz_without_assignment(self):
        self.client.force_login(self.security_officer)

        response = self.client.get(self._take_url())

        self.assertEqual(response.status_code, 200)

    def test_admin_can_preview_quiz_without_assignment(self):
        self.client.force_login(self.admin)

        response = self.client.get(self._take_url())

        self.assertEqual(response.status_code, 200)

    def test_option_from_another_question_is_rejected(self):
        self.client.force_login(self.employee)
        payload = self._valid_payload()
        payload[f'question_{self.question_one.pk}'] = str(
            self.question_two_correct.pk
        )

        response = self.client.post(self._take_url(), payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Submission.objects.count(), 0)
        self.assertEqual(Answer.objects.count(), 0)
        self.assertTrue(
            AuditLog.objects.filter(action='quiz_invalid_submission').exists()
        )

    def test_option_from_another_quiz_is_rejected(self):
        self.client.force_login(self.employee)
        payload = self._valid_payload()
        payload[f'question_{self.question_one.pk}'] = str(
            self.other_option.pk
        )

        response = self.client.post(self._take_url(), payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Submission.objects.count(), 0)
        self.assertEqual(Answer.objects.count(), 0)

    def test_unknown_option_is_rejected(self):
        self.client.force_login(self.employee)
        payload = self._valid_payload()
        payload[f'question_{self.question_one.pk}'] = '999999999'

        response = self.client.post(self._take_url(), payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Submission.objects.count(), 0)
        self.assertEqual(Answer.objects.count(), 0)

    def test_unknown_question_field_is_rejected(self):
        self.client.force_login(self.employee)
        payload = self._valid_payload()
        payload['question_999999999'] = str(self.question_one_correct.pk)

        response = self.client.post(self._take_url(), payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Submission.objects.count(), 0)

    def test_duplicate_answer_value_is_rejected(self):
        self.client.force_login(self.employee)
        payload = (
            f'question_{self.question_one.pk}='
            f'{self.question_one_correct.pk}&'
            f'question_{self.question_one.pk}='
            f'{self.question_one_wrong.pk}&'
            f'question_{self.question_two.pk}='
            f'{self.question_two_correct.pk}'
        )

        response = self.client.post(
            self._take_url(),
            payload,
            content_type='application/x-www-form-urlencoded',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Submission.objects.count(), 0)

    def test_valid_submission_creates_answers_and_score(self):
        self.client.force_login(self.employee)

        response = self.client.post(self._take_url(), self._valid_payload())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Submission.objects.count(), 1)
        self.assertEqual(Answer.objects.count(), 2)

        submission = Submission.objects.get()
        self.assertEqual(submission.score, 2)
        self.assertEqual(submission.percent, 100.0)
        self.assertTrue(submission.passed)
        self.assertEqual(submission.attempt_number, 1)

        self.assignment.refresh_from_db()
        self.assertEqual(
            self.assignment.status,
            CourseAssignment.Status.COMPLETED,
        )

    def test_attempt_limit_is_checked_before_submission(self):
        self.client.force_login(self.employee)
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

        response = self.client.post(self._take_url(), self._valid_payload())

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Submission.objects.count(), 1)

    def test_unpublished_course_quiz_is_rejected(self):
        self.client.force_login(self.employee)
        self.course.is_published = False
        self.course.save(update_fields=['is_published'])

        response = self.client.get(self._take_url())

        self.assertEqual(response.status_code, 403)
