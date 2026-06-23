from django.test import TestCase
from django.urls import reverse
from datetime import date

from assignments.models import CourseAssignment
from courses.models import Course, SecurityCategory, TrainingProgram
from tests.utils import create_user


class AccessTests(TestCase):
    def setUp(self):
        self.employee = create_user(
            'employee1',
            password='password123',
            role='employee',
            department_name='ИТ-отдел',
            position_name='Системный администратор',
        )
        self.security_officer = create_user('security1', password='password123', role='security_officer')
        self.admin = create_user('admin1', password='password123', role='admin')

        category = SecurityCategory.objects.create(code='phishing', name='Фишинг', description='Описание')
        program = TrainingProgram.objects.create(
            title='Антифишинг',
            category=category,
            description='Описание',
            is_mandatory=True,
            periodicity_days=365,
        )
        self.course = Course.objects.create(
            title='Основы ИБ',
            description='Описание',
            training_program=program,
            is_mandatory=True,
            validity_days=365,
            author=self.admin,
            is_published=True,
        )
        self.assignment = CourseAssignment.objects.create(
            employee=self.employee,
            course=self.course,
            assigned_by=self.security_officer,
            due_date=date(2030, 1, 1),
            status=CourseAssignment.Status.ASSIGNED,
        )

    def test_employee_can_view_own_assignments(self):
        self.client.login(username='employee1', password='password123')
        response = self.client.get(reverse('assignments:my'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.course.title)

    def test_employee_cannot_view_reports(self):
        self.client.login(username='employee1', password='password123')
        response = self.client.get(reverse('reports:dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_security_officer_can_view_reports(self):
        self.client.login(username='security1', password='password123')
        response = self.client.get(reverse('reports:dashboard'))
        self.assertEqual(response.status_code, 200)
