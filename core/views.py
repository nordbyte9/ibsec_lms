from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.permissions import Permission, has_permission

from assignments.models import CourseAssignment
from courses.models import Course
from quizzes.models import Submission

from .navigation import breadcrumbs

def home(request):
    user = request.user
    is_authenticated = user.is_authenticated
    can_view_reports = has_permission(user, Permission.VIEW_REPORTS)

    context = {
        'available_courses_count': Course.objects.filter(is_published=True).count(),
        'assigned_courses_count': CourseAssignment.objects.filter(employee=user).count() if is_authenticated else 0,
        'completed_tests_count': Submission.objects.filter(user=user).count() if is_authenticated else 0,
        'can_view_reports': can_view_reports,
        'breadcrumbs': breadcrumbs(('Главная', None)),
    }
    return render(request, 'core/home.html', context)


@login_required
def help_page(request):
    return render(
        request,
        'core/help.html',
        {
            'breadcrumbs': breadcrumbs(('Главная', '/'), ('Справка', None)),
        },
    )
