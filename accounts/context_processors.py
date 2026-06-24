from .permissions import Permission, has_permission


_PERMISSION_MAP = {
    "manage_courses": Permission.MANAGE_COURSES,
    "manage_assignments": Permission.MANAGE_ASSIGNMENTS,
    "manage_knowledge": Permission.MANAGE_KNOWLEDGE,
    "view_all_results": Permission.VIEW_ALL_RESULTS,
    "view_reports": Permission.VIEW_REPORTS,
    "export_reports": Permission.EXPORT_REPORTS,
    "view_audit": Permission.VIEW_AUDIT,
    "view_integrations": Permission.VIEW_INTEGRATIONS,
    "manage_users": Permission.MANAGE_USERS,
    "manage_system": Permission.MANAGE_SYSTEM,
}


def rbac_permissions(request):
    """Добавляет централизованные прикладные разрешения в шаблоны."""

    user = getattr(request, "user", None)
    permissions = {
        name: has_permission(user, permission)
        for name, permission in _PERMISSION_MAP.items()
    }
    permissions["security_staff"] = any(
        (
            permissions["manage_courses"],
            permissions["manage_assignments"],
            permissions["manage_knowledge"],
            permissions["view_all_results"],
            permissions["view_reports"],
            permissions["view_audit"],
            permissions["view_integrations"],
        )
    )
    return {"rbac": permissions}
