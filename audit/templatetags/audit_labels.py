from django import template


register = template.Library()


ACTION_LABELS = {
    'course_assigned': 'Назначение курса',
    'assignment_completed': 'Завершение обучения',
    'quiz_submitted': 'Сдача теста',
    'quiz_invalid_submission': 'Отклонение некорректных ответов',
    'quiz_attempt_started': 'Начало попытки теста',
    'quiz_attempt_expired': 'Истечение времени попытки',
    'csv_export': 'Экспорт отчёта CSV',
    'xlsx_export': 'Экспорт реестра XLSX',
    'docx_certificate': 'Формирование сертификата DOCX',
    'material_uploaded': 'Загрузка учебного материала',
    'material_downloaded': 'Скачивание учебного материала',
    'material_download_denied': 'Отказ в скачивании материала',
    'material_file_missing': 'Отсутствие файла в хранилище',
    'user_login': 'Вход пользователя',
    'user_logout': 'Выход пользователя',
    'course_created': 'Создание курса',
    'lesson_created': 'Создание урока',
}


OBJECT_LABELS = {
    'CourseAssignment': 'Назначение курса',
    'Submission': 'Результат теста',
    'Quiz': 'Тест',
    'QuizAttempt': 'Попытка теста',
    'Report': 'Отчёт',
    'Lesson': 'Урок',
    'Course': 'Курс',
    'User': 'Пользователь',
    'IntegrationSyncLog': 'Импорт организационной структуры',
}


OBJECT_REFERENCE_LABELS = {
    'training_registry': 'Реестр обучения',
    'employee_report': 'Отчёт по сотрудникам',
    'department_report': 'Отчёт по подразделениям',
    'course_report': 'Отчёт по курсам',
}


@register.filter
def audit_action_label(value):
    """Возвращает русское название действия журнала аудита."""

    if value in (None, ''):
        return 'Системное действие'

    return ACTION_LABELS.get(str(value), 'Другое действие')


@register.filter
def audit_object_label(value):
    """Возвращает русское название типа объекта журнала аудита."""

    if value in (None, ''):
        return 'Системный объект'

    return OBJECT_LABELS.get(str(value), 'Системный объект')


@register.filter
def audit_object_reference_label(value):
    """Переводит внутренний идентификатор объекта для интерфейса."""

    if value in (None, ''):
        return ''

    normalized_value = str(value).strip().lstrip('#')

    if normalized_value in OBJECT_REFERENCE_LABELS:
        return OBJECT_REFERENCE_LABELS[normalized_value]

    if normalized_value.isdigit():
        return f'№ {normalized_value}'

    return normalized_value
