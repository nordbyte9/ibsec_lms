import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render

from accounts.permissions import Permission, has_permission
from audit.services import log_action
from core.navigation import breadcrumbs
from .forms import OrganizationImportForm
from .models import IntegrationSyncLog
from .services import import_organization_file


def _can_view_integrations(user):
    return has_permission(user, Permission.VIEW_INTEGRATIONS)


@login_required
def integration_index(request):
    if not _can_view_integrations(request.user):
        return HttpResponseForbidden('Недостаточно прав')

    import_result = None
    if request.method == 'POST':
        form = OrganizationImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                import_result = import_organization_file(form.cleaned_data['data_file'])
                log_action(
                    request.user,
                    'organization_imported',
                    'IntegrationSyncLog',
                    import_result['log'].pk,
                    f'Импортирована организационная структура: обработано пользователей {import_result["processed_users"]}',
                    request=request,
                )
                messages.success(
                    request,
                    (
                        'Импорт завершён: обработано пользователей — '
                        f'{import_result["processed_users"]}, создано — {import_result["created_users"]}, '
                        f'обновлено — {import_result["updated_users"]}; '
                        f'новых подразделений — {import_result["created_departments"]}, '
                        f'новых должностей — {import_result["created_positions"]}.'
                    ),
                )
                return redirect('integrations:index')
            except Exception as exc:
                messages.error(request, f'Импорт не выполнен: {exc}')
    else:
        form = OrganizationImportForm()

    logs = IntegrationSyncLog.objects.order_by('-started_at', '-id')[:20]
    return render(
        request,
        'integrations/index.html',
        {
            'form': form,
            'logs': logs,
            'import_result': import_result,
            'breadcrumbs': breadcrumbs(('Главная', '/'), ('Импорт оргструктуры', None)),
        },
    )


@login_required
def download_sample(request):
    if not _can_view_integrations(request.user):
        return HttpResponseForbidden('Недостаточно прав')
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="organization_example.csv"'
    response.write('\ufeff')
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Имя пользователя', 'Электронная почта', 'Имя', 'Фамилия', 'Подразделение', 'Должность', 'Роль'])
    writer.writerow(['ivanov', 'ivanov@example.com', 'Иван', 'Иванов', 'Отдел информационной безопасности', 'Специалист', 'Сотрудник'])
    return response
