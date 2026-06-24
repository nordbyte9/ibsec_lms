from enum import Enum

from .models import Profile


class Permission(str, Enum):
    """Прикладные разрешения IBSec LMS."""

    VIEW_PUBLISHED_COURSES = "view_published_courses"
    VIEW_OWN_ASSIGNMENTS = "view_own_assignments"
    VIEW_OWN_RESULTS = "view_own_results"
    TAKE_ASSIGNED_QUIZ = "take_assigned_quiz"
    DOWNLOAD_OWN_CERTIFICATE = "download_own_certificate"
    DOWNLOAD_PROTECTED_MATERIAL = "download_protected_material"
    MANAGE_COURSES = "manage_courses"
    MANAGE_ASSIGNMENTS = "manage_assignments"
    MANAGE_KNOWLEDGE = "manage_knowledge"
    VIEW_ALL_RESULTS = "view_all_results"
    VIEW_REPORTS = "view_reports"
    EXPORT_REPORTS = "export_reports"
    VIEW_AUDIT = "view_audit"
    VIEW_INTEGRATIONS = "view_integrations"
    MANAGE_USERS = "manage_users"
    MANAGE_SYSTEM = "manage_system"


EMPLOYEE_PERMISSIONS = frozenset(
    {
        Permission.VIEW_PUBLISHED_COURSES,
        Permission.VIEW_OWN_ASSIGNMENTS,
        Permission.VIEW_OWN_RESULTS,
        Permission.TAKE_ASSIGNED_QUIZ,
        Permission.DOWNLOAD_OWN_CERTIFICATE,
        Permission.DOWNLOAD_PROTECTED_MATERIAL,
    }
)

SECURITY_OFFICER_PERMISSIONS = EMPLOYEE_PERMISSIONS | frozenset(
    {
        Permission.MANAGE_COURSES,
        Permission.MANAGE_ASSIGNMENTS,
        Permission.MANAGE_KNOWLEDGE,
        Permission.VIEW_ALL_RESULTS,
        Permission.VIEW_REPORTS,
        Permission.EXPORT_REPORTS,
        Permission.VIEW_AUDIT,
        Permission.VIEW_INTEGRATIONS,
    }
)

ADMIN_PERMISSIONS = frozenset(Permission)

ROLE_PERMISSIONS = {
    Profile.Role.EMPLOYEE.value: EMPLOYEE_PERMISSIONS,
    Profile.Role.SECURITY_OFFICER.value: SECURITY_OFFICER_PERMISSIONS,
    Profile.Role.ADMIN.value: ADMIN_PERMISSIONS,
}


def get_user_role(user):
    """Возвращает сохранённую в БД роль пользователя или None.

    Роль читается напрямую из Profile, а не через user.profile. Это исключает
    использование устаревшего объекта, который может остаться в reverse-cache
    после сигнала автоматического создания профиля.
    """

    if not getattr(user, "is_authenticated", False):
        return None
    user_id = getattr(user, "pk", None)
    if user_id is None:
        return None
    role = (
        Profile.objects.filter(user_id=user_id)
        .values_list("role", flat=True)
        .first()
    )
    if role is None:
        return None
    try:
        return Profile.Role(role).value
    except ValueError:
        return None


def has_permission(user, permission):
    """Проверяет прикладное разрешение пользователя."""

    if not getattr(user, "is_authenticated", False):
        return False
    if not getattr(user, "is_active", False):
        return False

    # Системный суперпользователь Django сохраняет полный доступ.
    if getattr(user, "is_superuser", False):
        return True

    try:
        normalized_permission = (
            permission if isinstance(permission, Permission) else Permission(permission)
        )
    except (TypeError, ValueError):
        return False

    role = get_user_role(user)
    role_permissions = ROLE_PERMISSIONS.get(role, frozenset())
    return normalized_permission in role_permissions


def has_any_permission(user, *permissions):
    """Проверяет наличие хотя бы одного разрешения."""

    return any(has_permission(user, permission) for permission in permissions)


def has_all_permissions(user, *permissions):
    """Проверяет наличие всех переданных разрешений."""

    return all(has_permission(user, permission) for permission in permissions)
