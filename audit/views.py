import re

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

from accounts.permissions import Permission, has_permission
from core.navigation import breadcrumbs
from .models import AuditLog


ACTION_LABELS = {
    'course_assigned': 'Назначен курс',
    'assignment_created': 'Создано назначение',
    'assignment_completed': 'Назначение завершено',
    'quiz_attempt_started': 'Начата попытка',
    'quiz_attempt_expired': 'Время попытки истекло',
    'quiz_submitted': 'Проверка завершена',
    'csv_export': 'Скачана таблица',
    'xlsx_export': 'Скачан реестр',
    'report_exported': 'Скачан отчёт',
    'organization_imported': 'Импортирована оргструктура',
    'material_uploaded': 'Загружен учебный материал',
    'material_downloaded': 'Скачан учебный материал',
    'material_download_denied': 'Отказано в скачивании материала',
    'material_file_missing': 'Файл материала не найден',
    'protected_file_downloaded': 'Скачан защищённый файл',
    'file_downloaded': 'Скачан файл',
    'article_opened': 'Открыта статья',
}

OBJECT_LABELS = {
    'CourseAssignment': 'Назначение курса',
    'course_assignment': 'Назначение курса',
    'QuizAttempt': 'Попытка проверки',
    'quiz_attempt': 'Попытка проверки',
    'Submission': 'Результат проверки',
    'Report': 'Отчёт',
    'report': 'Отчёт',
    'IntegrationSyncLog': 'Операция импорта',
    'Course': 'Курс',
    'Lesson': 'Урок',
    'User': 'Пользователь',
    'Article': 'Статья',
    'ProtectedFile': 'Защищённый файл',
}

IDENTIFIER_LABELS = {
    'training_registry': 'Реестр обучения',
    'employee_report': 'Отчёт по сотрудникам',
    'department_report': 'Отчёт по подразделениям',
    'course_report': 'Отчёт по курсам',
}

DESCRIPTION_REPLACEMENTS = {
    'Экспортирован XLSX-реестр': 'Сформирован реестр обучения',
    'Экспортирован CSV-отчёт': 'Сформирована таблица отчёта',
    'XLSX-реестр': 'реестр обучения',
    'XLSX': 'реестр',
    'CSV': 'таблица',
    'QuizAttempt': 'попытка проверки',
    'Submission': 'результат проверки',
    'Report': 'отчёт',
    'training_registry': 'реестр обучения',
}


def _can_view_audit(user):
    return has_permission(user, Permission.VIEW_AUDIT)


def _translate_description(value):
    if not value:
        return 'Описание отсутствует'
    translated = value
    for source, target in DESCRIPTION_REPLACEMENTS.items():
        translated = translated.replace(source, target)
    # Служебные коды не должны отображаться пользователю.
    translated = re.sub(r'\b[a-z]+(?:_[a-z]+)+\b', 'служебная запись', translated)
    return translated


def _translate_identifier(value):
    if not value:
        return ''
    if value in IDENTIFIER_LABELS:
        return IDENTIFIER_LABELS[value]
    if str(value).isdigit():
        return f'№ {value}'
    return 'Служебная запись'


@login_required
def audit_log_list(request):
    if not _can_view_audit(request.user):
        return HttpResponseForbidden('Недостаточно прав')

    logs = AuditLog.objects.select_related('user', 'user__profile').all()
    action = request.GET.get('action', '').strip()
    object_type = request.GET.get('object_type', '').strip()
    if action:
        logs = logs.filter(action=action)
    if object_type:
        logs = logs.filter(object_type=object_type)

    prepared_logs = []
    for log in logs:
        log.action_label = ACTION_LABELS.get(log.action, 'Системное действие')
        log.object_type_label = OBJECT_LABELS.get(log.object_type, 'Системный объект')
        log.object_id_label = _translate_identifier(log.object_id)
        log.display_description = _translate_description(log.description)
        prepared_logs.append(log)

    return render(
        request,
        'audit/audit_log_list.html',
        {
            'logs': prepared_logs,
            'selected_action': action,
            'selected_object_type': object_type,
            'action_choices': ACTION_LABELS.items(),
            'object_choices': OBJECT_LABELS.items(),
            'breadcrumbs': breadcrumbs(('Главная', '/'), ('Журнал аудита', None)),
        },
    )
