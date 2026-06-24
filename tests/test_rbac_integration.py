from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from tests.utils import create_user


class CentralizedRbacIntegrationTests(TestCase):
    def setUp(self):
        self.employee = create_user(
            'rbac_employee',
            password='password123',
            role=Profile.Role.EMPLOYEE,
        )
        self.security_officer = create_user(
            'rbac_security',
            password='password123',
            role=Profile.Role.SECURITY_OFFICER,
        )
        self.admin = create_user(
            'rbac_admin',
            password='password123',
            role=Profile.Role.ADMIN,
        )

    def _assert_statuses(self, user, expected_status, route_names):
        self.client.force_login(user)

        for route_name in route_names:
            with self.subTest(user=user.username, route=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, expected_status)

        self.client.logout()

    def test_employee_cannot_open_staff_sections(self):
        self._assert_statuses(
            self.employee,
            403,
            (
                'assignments:list',
                'audit:list',
                'integrations:index',
                'reports:dashboard',
                'reports:training_registry_xlsx',
            ),
        )

    def test_security_officer_can_open_staff_sections(self):
        self._assert_statuses(
            self.security_officer,
            200,
            (
                'assignments:list',
                'audit:list',
                'integrations:index',
                'reports:dashboard',
                'reports:training_registry_xlsx',
            ),
        )

    def test_admin_can_open_staff_sections(self):
        self._assert_statuses(
            self.admin,
            200,
            (
                'assignments:list',
                'audit:list',
                'integrations:index',
                'reports:dashboard',
                'reports:training_registry_xlsx',
            ),
        )

    def test_employee_template_context_contains_no_staff_permissions(self):
        self.client.force_login(self.employee)
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['rbac']['security_staff'])
        self.assertFalse(response.context['rbac']['manage_courses'])
        self.assertFalse(response.context['rbac']['view_reports'])
        self.assertFalse(response.context['rbac']['view_audit'])

    def test_security_officer_template_context_contains_staff_permissions(self):
        self.client.force_login(self.security_officer)
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['rbac']['security_staff'])
        self.assertTrue(response.context['rbac']['manage_courses'])
        self.assertTrue(response.context['rbac']['view_reports'])
        self.assertTrue(response.context['rbac']['view_audit'])

    def test_course_create_link_is_hidden_from_employee(self):
        self.client.force_login(self.employee)
        response = self.client.get(reverse('courses:list'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Создать курс')

    def test_course_create_link_is_visible_to_security_officer(self):
        self.client.force_login(self.security_officer)
        response = self.client.get(reverse('courses:list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Создать курс')
