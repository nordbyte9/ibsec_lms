from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from courses.models import Course, SecurityCategory, TrainingProgram
from tests.utils import create_user


class CourseCatalogDesignTests(TestCase):
    def setUp(self):
        self.employee = create_user(
            'catalog_employee',
            password='password123',
            role=Profile.Role.EMPLOYEE,
        )
        self.admin = create_user(
            'catalog_admin',
            password='password123',
            role=Profile.Role.ADMIN,
        )
        category = SecurityCategory.objects.create(
            code='catalog-security',
            name='Информационная безопасность',
        )
        program = TrainingProgram.objects.create(
            title='Базовая программа ИБ',
            category=category,
            is_mandatory=True,
        )
        self.course = Course.objects.create(
            title='Основы информационной безопасности',
            description='Базовый курс для сотрудников организации.',
            training_program=program,
            is_mandatory=True,
            validity_days=365,
            author=self.admin,
            is_published=True,
        )

    def test_catalog_renders_russian_interface_and_course_image(self):
        self.client.force_login(self.employee)

        response = self.client.get(reverse('courses:list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Каталог курсов')
        self.assertContains(response, 'Все курсы')
        self.assertContains(response, 'Только обязательные')
        self.assertContains(response, 'Открыть курс')
        self.assertContains(response, 'img/courses/')
        self.assertNotContains(response, '>Catalog<')
        self.assertNotContains(response, '>Filters<')

    def test_employee_does_not_see_create_course_button(self):
        self.client.force_login(self.employee)

        response = self.client.get(reverse('courses:list'))

        self.assertNotContains(response, 'Создать курс')

    def test_admin_sees_create_course_button(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('courses:list'))

        self.assertContains(response, 'Создать курс')
