from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

from core.navigation import breadcrumbs

from .models import AuditLog


def _can_view_audit(user):
    return user.is_authenticated and user.profile.role in ('security_officer', 'admin')


@login_required
def audit_log_list(request):
    if not _can_view_audit(request.user):
        return HttpResponseForbidden('Недостаточно прав')

    logs = AuditLog.objects.select_related('user').all()
    action = request.GET.get('action')
    object_type = request.GET.get('object_type')
    if action:
        logs = logs.filter(action=action)
    if object_type:
        logs = logs.filter(object_type=object_type)

    return render(
        request,
        'audit/audit_log_list.html',
        {
            'logs': logs,
            'selected_action': action or '',
            'selected_object_type': object_type or '',
            'breadcrumbs': breadcrumbs(('Главная', '/'), ('Журнал аудита', None)),
        },
    )
