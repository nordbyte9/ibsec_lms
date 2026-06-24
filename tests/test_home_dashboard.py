from datetime import timedelta
import re

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from assignments.models import CourseAssignment
from courses.models import Course
from quizzes.models import Quiz, Submission
from tests.utils import create_user


class HomeDashboardTests(TestCase):
    def setUp(self):
        self.employee = create_user(
            'home_employee',
            password='password123',
            role='employee',
        )
        self.admin = create_user(
            'home_admin',
            password='password123',
            role='admin',
        )
        self.course = Course.objects.create(
            title='Основы информационной безопасности',
            description='Учебный курс',
            author=self.admin,
            is_published=True,
            is_mandatory=True,
        )
        self.assignment = CourseAssignment.objects.create(
            employee=self.employee,
            course=self.course,
            assigned_by=self.admin,
            due_date=timezone.localdate() + timedelta(days=7),
            status=CourseAssignment.Status.IN_PROGRESS,
        )
        self.quiz = Quiz.objects.create(
            course=self.course,
            title='Итоговый тест',
            pass_score=70,
            is_active=True,
        )
        Submission.objects.create(
            user=self.employee,
            quiz=self.quiz,
            score=3,
            percent=100.0,
            passed=True,
            attempt_number=1,
        )

    def test_authenticated_home_contains_real_learning_data(self):
        self.client.force_login(self.employee)

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Добро пожаловать')
        self.assertContains(response, self.course.title)
        self.assertContains(response, '100%')
        self.assertContains(response, 'Ближайшие сроки')
        self.assertContains(response, 'Последние результаты')

    def test_home_has_no_english_dashboard_labels(self):
        self.client.force_login(self.employee)

        response = self.client.get(reverse('home'))
        content = response.content.decode('utf-8')
        content = re.sub(r"<(script|style)\b.*?</\1>", " ", content, flags=re.S | re.I)
        content = re.sub(r"<[^>]+>", " ", content)
        visible_text = " ".join(content.split()).lower()

        self.assertNotIn('dashboard', visible_text)
        self.assertNotIn('my courses', visible_text)
        self.assertNotIn('progress overview', visible_text)

    def test_anonymous_home_shows_public_login_screen(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Корпоративная система обучения')
        self.assertContains(response, 'Войти в систему')
        self.assertNotContains(response, reverse('courses:list'))
        self.assertNotContains(response, 'Мои назначения')
