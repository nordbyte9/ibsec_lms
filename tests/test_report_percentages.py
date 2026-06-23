import csv
import io

from django.test import TestCase
from django.urls import reverse

from courses.models import Course
from quizzes.models import Quiz, Submission
from tests.utils import create_user


class ReportPercentageTests(TestCase):
    def setUp(self):
        self.employee = create_user('report_employee', role='employee')
        self.admin = create_user('report_admin', role='admin')
        self.course = Course.objects.create(
            title='Курс для проверки процентов',
            author=self.admin,
            is_published=True,
        )
        self.quiz = Quiz.objects.create(
            course=self.course,
            title='Тест по основам ИБ',
        )

    def test_my_progress_displays_percent_not_raw_score(self):
        Submission.objects.create(
            user=self.employee,
            quiz=self.quiz,
            score=3,
            percent=100.0,
            passed=True,
            attempt_number=1,
        )

        self.client.force_login(self.employee)
        response = self.client.get(reverse('reports:my_progress'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '100%')
        self.assertNotContains(response, '>3%</td>')

    def test_course_report_averages_percent_values(self):
        Submission.objects.create(
            user=self.employee,
            quiz=self.quiz,
            score=3,
            percent=100.0,
            passed=True,
            attempt_number=1,
        )
        Submission.objects.create(
            user=self.employee,
            quiz=self.quiz,
            score=1,
            percent=50.0,
            passed=False,
            attempt_number=2,
        )

        self.client.force_login(self.admin)
        response = self.client.get(
            reverse('reports:course_report'),
            {'course': self.course.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['rows'][0]['avg_percent'], 75.0)

    def test_course_csv_exports_average_percent(self):
        Submission.objects.create(
            user=self.employee,
            quiz=self.quiz,
            score=3,
            percent=100.0,
            passed=True,
            attempt_number=1,
        )
        Submission.objects.create(
            user=self.employee,
            quiz=self.quiz,
            score=1,
            percent=50.0,
            passed=False,
            attempt_number=2,
        )

        self.client.force_login(self.admin)
        response = self.client.get(
            reverse('reports:course_export_csv'),
            {'course': self.course.pk},
        )

        self.assertEqual(response.status_code, 200)
        rows = list(csv.reader(io.StringIO(response.content.decode('utf-8'))))
        self.assertEqual(rows[0][-1], 'Средний результат, %')
        self.assertEqual(rows[1][-1], '75.0')
