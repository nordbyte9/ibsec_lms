from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

from .models import IntegrationSyncLog


def _can_view_integrations(user):
    return user.is_authenticated and user.profile.role in ('security_officer', 'admin')


@login_required
def integration_index(request):
    if not _can_view_integrations(request.user):
        return HttpResponseForbidden('Недостаточно прав')

    logs = IntegrationSyncLog.objects.order_by('-started_at', '-id')[:20]
    return render(
        request,
        'integrations/index.html',
        {
            'logs': logs,
        },
    )
