from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from .models import Course, Lesson
from .forms import CourseForm, LessonForm
from core.navigation import breadcrumbs

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
        {'courses': courses, 'breadcrumbs': breadcrumbs(('Главная', '/'), ('Курсы', None))},
    )

@login_required
def course_detail(request, pk):
    course = get_object_or_404(
        Course.objects.select_related('training_program', 'training_program__category', 'author')
        .prefetch_related('lessons', 'target_departments', 'target_positions'),
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
            'breadcrumbs': breadcrumbs(('Главная', '/'), ('Курсы', '/courses/'), (course.title, None)),
        },
    )

@login_required
def course_create(request):
    if request.user.profile.role not in ('security_officer', 'admin'):
        return HttpResponseForbidden('Недостаточно прав')
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
        {'form': form, 'breadcrumbs': breadcrumbs(('Главная', '/'), ('Курсы', '/courses/'), ('Создать курс', None))},
    )

@login_required
def lesson_create(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if request.user.profile.role not in ('security_officer', 'admin'):
        return HttpResponseForbidden('Недостаточно прав')
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
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
