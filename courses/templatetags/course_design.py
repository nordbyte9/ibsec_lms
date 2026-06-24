from __future__ import annotations

from pathlib import Path

from django import template

from assignments.models import CourseAssignment
from quizzes.models import Submission

register = template.Library()


_IMAGE_RULES = (
    (('основы информационной безопасности', 'основы безопасности'), 'img/courses/osnovy-informatsionnoy-bezopasnosti.webp'),
    (('фишинг', 'социальн'), 'img/courses/zashchita-ot-fishinga.webp'),
    (('парол', 'аутентиф'), 'img/courses/paroli-i-autentifikatsiya.webp'),
    (('сетев', 'облак', 'vpn', 'удален'), 'img/courses/setevaya-bezopasnost.webp'),
    (('доступ', 'привилег', 'учетн'), 'img/courses/upravlenie-dostupom.webp'),
    (('осведом', 'сотрудник', 'кибергигиен'), 'img/courses/kiberbezopasnost-sotrudnikov.webp'),
)

_STATUS_LABELS = {
    CourseAssignment.Status.ASSIGNED: ('Назначен', 'назначен'),
    CourseAssignment.Status.IN_PROGRESS: ('В процессе', 'в-процессе'),
    CourseAssignment.Status.COMPLETED: ('Завершён', 'завершен'),
    CourseAssignment.Status.OVERDUE: ('Просрочен', 'просрочен'),
}

_LESSON_TYPE_LABELS = {
    'text': 'Материал для чтения',
    'link': 'Внешний материал',
    'file': 'Файл для скачивания',
}


def _course_image(course):
    searchable = ' '.join(
        value
        for value in (
            course.title,
            course.description,
            getattr(getattr(course, 'training_program', None), 'title', ''),
            getattr(
                getattr(getattr(course, 'training_program', None), 'category', None),
                'name',
                '',
            ),
        )
        if value
    ).lower()

    for keywords, image_path in _IMAGE_RULES:
        if any(keyword in searchable for keyword in keywords):
            return image_path

    return 'img/courses/osnovy-informatsionnoy-bezopasnosti.webp'


def _course_category(course):
    program = getattr(course, 'training_program', None)
    category = getattr(program, 'category', None)
    return getattr(category, 'name', None) or 'Общее обучение'


def _assignment_for_user(course, user):
    if not user or not user.is_authenticated:
        return None

    return (
        CourseAssignment.objects.filter(employee=user, course=course)
        .order_by('-assigned_at', '-id')
        .first()
    )


def _latest_submission(course, user):
    if not user or not user.is_authenticated:
        return None

    return (
        Submission.objects.filter(user=user, quiz__course=course)
        .select_related('quiz')
        .order_by('-taken_at', '-id')
        .first()
    )


@register.simple_tag(takes_context=True)
def course_catalog_cards(context, courses):
    """Подготавливает карточки каталога без изменения модели курса."""

    request = context.get('request')
    user = getattr(request, 'user', None)
    course_list = list(courses)
    course_ids = [course.pk for course in course_list]

    assignments = {}
    results = {}

    if user and user.is_authenticated and course_ids:
        for assignment in CourseAssignment.objects.filter(
            employee=user,
            course_id__in=course_ids,
        ).select_related('course').order_by('-id'):
            assignments.setdefault(assignment.course_id, assignment)

        for submission in Submission.objects.filter(
            user=user,
            quiz__course_id__in=course_ids,
        ).select_related('quiz', 'quiz__course').order_by('-taken_at', '-id'):
            results.setdefault(submission.quiz.course_id, submission)

    cards = []
    for course in course_list:
        assignment = assignments.get(course.pk)
        result = results.get(course.pk)
        status_label = 'Доступен'
        status_class = 'доступен'

        if assignment:
            status_label, status_class = _STATUS_LABELS.get(
                assignment.status,
                ('Назначен', 'назначен'),
            )

        cards.append(
            {
                'course': course,
                'image': _course_image(course),
                'category': _course_category(course),
                'category_key': _course_category(course).lower(),
                'status_label': status_label,
                'status_class': status_class,
                'is_assigned': assignment is not None,
                'latest_percent': (
                    int(round(result.percent)) if result is not None else None
                ),
                'is_passed': bool(result and result.passed),
            }
        )

    return cards


@register.simple_tag
def course_catalog_summary(cards):
    categories = []
    for card in cards:
        if card['category'] not in categories:
            categories.append(card['category'])

    return {
        'total': len(cards),
        'mandatory': sum(1 for card in cards if card['course'].is_mandatory),
        'assigned': sum(1 for card in cards if card['is_assigned']),
        'categories': categories,
    }


@register.simple_tag(takes_context=True)
def course_detail_summary(context, course):
    """Возвращает реальные сведения для страницы курса."""

    request = context.get('request')
    user = getattr(request, 'user', None)
    assignment = _assignment_for_user(course, user)
    result = _latest_submission(course, user)
    status_label = 'Доступен'
    status_class = 'доступен'

    if assignment:
        status_label, status_class = _STATUS_LABELS.get(
            assignment.status,
            ('Назначен', 'назначен'),
        )

    lessons = list(course.lessons.all())
    file_count = sum(1 for lesson in lessons if lesson.file and lesson.file_active)
    link_count = sum(1 for lesson in lessons if lesson.type == 'link')

    return {
        'image': _course_image(course),
        'category': _course_category(course),
        'assignment': assignment,
        'status_label': status_label,
        'status_class': status_class,
        'latest_percent': int(round(result.percent)) if result else None,
        'latest_passed': bool(result and result.passed),
        'lesson_count': len(lessons),
        'file_count': file_count,
        'link_count': link_count,
        'quiz_count': course.quizzes.filter(is_active=True).count(),
    }


@register.filter
def lesson_type_label(value):
    return _LESSON_TYPE_LABELS.get(value, 'Учебный материал')


@register.filter
def file_kind(filename):
    extension = Path(str(filename or '')).suffix.lower().lstrip('.')
    labels = {
        'pdf': 'Документ PDF',
        'docx': 'Документ',
        'xlsx': 'Электронная таблица',
        'pptx': 'Презентация',
        'txt': 'Текстовый файл',
        'csv': 'Табличные данные',
        'jpg': 'Изображение',
        'jpeg': 'Изображение',
        'png': 'Изображение',
    }
    return labels.get(extension, 'Файл')
