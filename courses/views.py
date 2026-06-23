from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import permission_required
from accounts.permissions import Permission
from audit.services import log_action
from core.navigation import breadcrumbs

from .access import (
    can_download_course_materials,
    can_download_lesson_material,
    can_manage_courses,
)
from .forms import CourseForm, LessonForm
from .models import Course, Lesson


@login_required
def course_list(request):
    courses = (
        Course.objects.filter(is_published=True)
        .select_related('training_program', 'training_program__category', 'author')
        .prefetch_related('target_departments', 'target_positions')
        .order_by('-created_at')
    )
    return render(
        request,
        'courses/course_list.html',
        {
            'courses': courses,
            'breadcrumbs': breadcrumbs(('Главная', '/'), ('Курсы', None)),
        },
    )


@login_required
def course_detail(request, pk):
    course = get_object_or_404(
        Course.objects.select_related(
            'training_program',
            'training_program__category',
            'author',
        ).prefetch_related(
            'lessons',
            'target_departments',
            'target_positions',
        ),
        pk=pk,
        is_published=True,
    )
    lessons = course.lessons.all()
    return render(
        request,
        'courses/course_detail.html',
        {
            'course': course,
            'lessons': lessons,
            'can_manage_courses': can_manage_courses(request.user),
            'can_download_materials': can_download_course_materials(
                request.user,
                course,
            ),
            'breadcrumbs': breadcrumbs(
                ('Главная', '/'),
                ('Курсы', '/courses/'),
                (course.title, None),
            ),
        },
    )


@permission_required(Permission.MANAGE_COURSES)
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.save()
            form.save_m2m()
            return redirect('courses:detail', obj.pk)
    else:
        form = CourseForm()

    return render(
        request,
        'courses/course_create.html',
        {
            'form': form,
            'breadcrumbs': breadcrumbs(
                ('Главная', '/'),
                ('Курсы', '/courses/'),
                ('Создать курс', None),
            ),
        },
    )


@permission_required(Permission.MANAGE_COURSES)
def lesson_create(request, course_id):
    course = get_object_or_404(Course, pk=course_id)

    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            if lesson.file:
                lesson.file_uploaded_by = request.user
            lesson.save()

            if lesson.file:
                log_action(
                    request.user,
                    'material_uploaded',
                    'Lesson',
                    lesson.pk,
                    (
                        f'Загружен защищённый материал «{lesson.download_filename}» '
                        f'для курса «{course.title}».'
                    ),
                    request,
                )

            return redirect('courses:detail', course.pk)
    else:
        form = LessonForm()

    return render(
        request,
        'courses/lesson_form.html',
        {
            'form': form,
            'course': course,
            'breadcrumbs': breadcrumbs(
                ('Главная', '/'),
                ('Курсы', '/courses/'),
                (course.title, f'/courses/{course.pk}/'),
                ('Добавить урок', None),
            ),
        },
    )


@login_required
def lesson_file_download(request, lesson_id):
    lesson = get_object_or_404(
        Lesson.objects.select_related('course'),
        pk=lesson_id,
        file_active=True,
    )

    if not lesson.file:
        raise Http404('Файл не найден.')

    if not can_download_lesson_material(request.user, lesson):
        log_action(
            request.user,
            'material_download_denied',
            'Lesson',
            lesson.pk,
            f'Отказано в скачивании материала курса «{lesson.course.title}».',
            request,
        )
        return HttpResponseForbidden('Недостаточно прав для скачивания файла.')

    try:
        file_handle = lesson.file.open('rb')
    except (FileNotFoundError, OSError):
        log_action(
            request.user,
            'material_file_missing',
            'Lesson',
            lesson.pk,
            f'Файл материала «{lesson.download_filename}» отсутствует в хранилище.',
            request,
        )
        raise Http404('Файл отсутствует в хранилище.')

    log_action(
        request.user,
        'material_downloaded',
        'Lesson',
        lesson.pk,
        (
            f'Скачан защищённый материал «{lesson.download_filename}» '
            f'курса «{lesson.course.title}».'
        ),
        request,
    )

    response = FileResponse(
        file_handle,
        as_attachment=True,
        filename=lesson.download_filename,
        content_type=lesson.file_content_type or 'application/octet-stream',
    )
    response['Cache-Control'] = 'private, no-store'
    response['Pragma'] = 'no-cache'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Content-Security-Policy'] = 'sandbox'
    return response
