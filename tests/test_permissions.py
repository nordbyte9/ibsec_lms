from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase

from accounts.models import Profile
from accounts.permissions import (
    Permission,
    has_all_permissions,
    has_any_permission,
    has_permission,
)
from tests.utils import create_user


class RolePermissionTests(TestCase):
    def setUp(self):
        self.employee = create_user(
            'permission_employee',
            password='password123',
            role=Profile.Role.EMPLOYEE,
        )
        self.security_officer = create_user(
            'permission_security',
            password='password123',
            role=Profile.Role.SECURITY_OFFICER,
        )
        self.admin = create_user(
            'permission_admin',
            password='password123',
            role=Profile.Role.ADMIN,
        )

    def test_employee_has_personal_permissions(self):
        self.assertTrue(
            has_permission(
                self.employee,
                Permission.VIEW_OWN_ASSIGNMENTS,
            )
        )
        self.assertTrue(
            has_permission(
                self.employee,
                Permission.TAKE_ASSIGNED_QUIZ,
            )
        )
        self.assertFalse(
            has_permission(
                self.employee,
                Permission.MANAGE_COURSES,
            )
        )
        self.assertFalse(
            has_permission(
                self.employee,
                Permission.VIEW_REPORTS,
            )
        )

    def test_security_officer_has_management_permissions(self):
        self.assertTrue(
            has_permission(
                self.security_officer,
                Permission.MANAGE_COURSES,
            )
        )
        self.assertTrue(
            has_permission(
                self.security_officer,
                Permission.MANAGE_ASSIGNMENTS,
            )
        )
        self.assertTrue(
            has_permission(
                self.security_officer,
                Permission.VIEW_REPORTS,
            )
        )
        self.assertTrue(
            has_permission(
                self.security_officer,
                Permission.VIEW_AUDIT,
            )
        )
        self.assertFalse(
            has_permission(
                self.security_officer,
                Permission.MANAGE_USERS,
            )
        )

    def test_admin_has_all_permissions(self):
        for permission in Permission:
            with self.subTest(permission=permission):
                self.assertTrue(has_permission(self.admin, permission))

    def test_anonymous_user_has_no_permissions(self):
        anonymous_user = AnonymousUser()

        self.assertFalse(
            has_permission(
                anonymous_user,
                Permission.VIEW_PUBLISHED_COURSES,
            )
        )

    def test_inactive_user_has_no_permissions(self):
        self.employee.is_active = False
        self.employee.save(update_fields=['is_active'])

        self.assertFalse(
            has_permission(
                self.employee,
                Permission.VIEW_OWN_ASSIGNMENTS,
            )
        )

    def test_unknown_permission_is_rejected(self):
        self.assertFalse(
            has_permission(
                self.admin,
                'unknown_permission',
            )
        )

    def test_saved_role_is_used_when_user_profile_cache_is_stale(self):
        cached_profile = self.employee.profile

        Profile.objects.filter(pk=cached_profile.pk).update(
            role=Profile.Role.ADMIN,
        )

        # Объект в reverse-cache по-прежнему содержит старую роль.
        self.assertEqual(cached_profile.role, Profile.Role.EMPLOYEE)

        # Проверка прав должна использовать сохранённую в БД роль.
        self.assertTrue(
            has_permission(
                self.employee,
                Permission.MANAGE_SYSTEM,
            )
        )

    def test_superuser_has_all_permissions_without_profile(self):
        superuser = User.objects.create_superuser(
            username='permission_root',
            email='root@example.com',
            password='password123',
        )

        self.assertTrue(
            has_permission(
                superuser,
                Permission.MANAGE_SYSTEM,
            )
        )

    def test_has_any_permission(self):
        self.assertTrue(
            has_any_permission(
                self.employee,
                Permission.MANAGE_COURSES,
                Permission.VIEW_OWN_ASSIGNMENTS,
            )
        )

    def test_has_all_permissions(self):
        self.assertTrue(
            has_all_permissions(
                self.security_officer,
                Permission.VIEW_REPORTS,
                Permission.EXPORT_REPORTS,
            )
        )
        self.assertFalse(
            has_all_permissions(
                self.employee,
                Permission.VIEW_OWN_RESULTS,
                Permission.VIEW_REPORTS,
            )
        )
