from datetime import date

from django.test import TestCase
from django.urls import reverse

from assignments.models import CourseAssignment
from courses.models import Course, Lesson, SecurityCategory, TrainingProgram
from quizzes.models import Option, Question, Quiz, Submission
from tests.utils import create_user


class CourseDetailDesignTests(TestCase):
    def setUp(self):
        self.employee = create_user(
            'detail_employee',
            password='password123',
            role='employee',
        )
        self.security_officer = create_user(
            'detail_security',
            password='password123',
            role='security_officer',
        )
        self.admin = create_user(
            'detail_admin',
            password='password123',
            role='admin',
        )

        category = SecurityCategory.objects.create(
            code='course-detail',
            name='Основы безопасности',
        )
        program = TrainingProgram.objects.create(
            title='Базовая программа обучения',
            category=category,
            description='Программа для сотрудников',
            is_mandatory=True,
        )
        self.course = Course.objects.create(
            title='Основы информационной безопасности',
            description='Практический курс для сотрудников организации.',
            training_program=program,
            is_mandatory=True,
            validity_days=365,
            author=self.security_officer,
            is_published=True,
        )
        Lesson.objects.create(
            course=self.course,
            title='Основные угрозы',
            content='Разбор основных угроз информационной безопасности.',
            type='text',
            order=1,
        )
        Lesson.objects.create(
            course=self.course,
            title='Дополнительные рекомендации',
            content='https://example.com/security-guide',
            type='link',
            order=2,
        )
        self.quiz = Quiz.objects.create(
            course=self.course,
            title='Итоговая проверка знаний',
            pass_score=70,
            is_active=True,
        )
        question = Question.objects.create(
            quiz=self.quiz,
            text='Какой пароль является более надёжным?',
        )
        Option.objects.create(
            question=question,
            text='Длинная уникальная парольная фраза',
            is_correct=True,
        )
        CourseAssignment.objects.create(
            employee=self.employee,
            course=self.course,
            assigned_by=self.security_officer,
            due_date=date(2030, 1, 1),
            status=CourseAssignment.Status.IN_PROGRESS,
        )
        Submission.objects.create(
            user=self.employee,
            quiz=self.quiz,
            score=1,
            percent=100.0,
            passed=True,
            attempt_number=1,
        )

    def test_employee_sees_russian_course_page_and_real_result(self):
        self.client.force_login(self.employee)

        response = self.client.get(
            reverse('courses:detail', args=[self.course.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Уроки и материалы')
        self.assertContains(response, 'Основные угрозы')
        self.assertContains(response, 'Дополнительные рекомендации')
        self.assertContains(response, 'Последний результат')
        self.assertContains(response, '100%')
        self.assertContains(response, 'В процессе')
        self.assertContains(response, 'Перейти к проверке знаний')
        self.assertContains(response, 'Развернуть все')
        self.assertNotContains(response, 'Добавить урок')

    def test_security_officer_sees_lesson_management_action(self):
        self.client.force_login(self.security_officer)

        response = self.client.get(
            reverse('courses:detail', args=[self.course.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Добавить урок')

    def test_empty_course_has_clear_empty_state(self):
        empty_course = Course.objects.create(
            title='Курс без материалов',
            description='',
            author=self.admin,
            is_published=True,
        )
        self.client.force_login(self.employee)

        response = self.client.get(
            reverse('courses:detail', args=[empty_course.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Материалы пока не добавлены')
        self.assertContains(response, 'Описание курса будет добавлено позже.')

    def test_course_page_uses_theme_image_from_static_storage(self):
        self.client.force_login(self.employee)

        response = self.client.get(
            reverse('courses:detail', args=[self.course.pk])
        )

        self.assertContains(
            response,
            'img/courses/osnovy-informatsionnoy-bezopasnosti.webp',
        )
