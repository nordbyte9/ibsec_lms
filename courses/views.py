from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from .models import Course, Lesson
from .forms import CourseForm, LessonForm

@login_required
def course_list(request):
    courses = Course.objects.filter(is_published=True).order_by('-created_at')
    return render(request, 'courses/course_list.html', {'courses': courses})

@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk, is_published=True)
    lessons = course.lessons.all()
    return render(request, 'courses/course_detail.html', {'course': course, 'lessons': lessons})

@login_required
def course_create(request):
    if request.user.profile.role not in ('instructor','admin'):
        return HttpResponseForbidden('Недостаточно прав')
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.save()
            return redirect('courses:detail', obj.pk)
    else:
        form = CourseForm()
    return render(request, 'courses/course_create.html', {'form': form})

@login_required
def lesson_create(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if request.user.profile.role not in ('instructor','admin'):
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
    return render(request, 'courses/lesson_form.html', {'form': form, 'course': course})
