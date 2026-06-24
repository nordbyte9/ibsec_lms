from django.db.models import Avg
from django.utils import timezone

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from accounts.permissions import Permission, has_permission
from assignments.models import CourseAssignment
from courses.models import Course
from quizzes.models import Submission

from .navigation import breadcrumbs


def _assignment_progress(assignment, submission_by_course):
    submission = submission_by_course.get(assignment.course_id)
    if submission is not None:
        return max(0, min(100, round(submission.percent)))
    if assignment.status == CourseAssignment.Status.COMPLETED:
        return 100
    return 0


def home(request):
    user = request.user
    is_authenticated = user.is_authenticated

    context = {
        'available_courses_count': Course.objects.filter(is_published=True).count(),
        'assigned_courses_count': 0,
        'completed_courses_count': 0,
        'overdue_courses_count': 0,
        'completion_percent': 0,
        'average_result': 0,
        'passed_tests_count': 0,
        'active_assignments': [],
        'upcoming_assignments': [],
        'recent_submissions': [],
        'can_view_reports': has_permission(user, Permission.VIEW_REPORTS),
        'can_manage_courses': has_permission(user, Permission.MANAGE_COURSES),
        'can_manage_assignments': has_permission(user, Permission.MANAGE_ASSIGNMENTS),
        'breadcrumbs': breadcrumbs(('Главная', None)),
    }

    if is_authenticated:
        assignments = list(
            CourseAssignment.objects.filter(employee=user)
            .select_related('course', 'course__training_program')
            .order_by('due_date', '-assigned_at')
        )
        submissions = list(
            Submission.objects.filter(user=user)
            .select_related('quiz', 'quiz__course')
            .order_by('-taken_at')
        )

        submission_by_course = {}
        for submission in submissions:
            submission_by_course.setdefault(submission.quiz.course_id, submission)

        assigned_count = len(assignments)
        completed_count = sum(
            assignment.status == CourseAssignment.Status.COMPLETED
            for assignment in assignments
        )
        overdue_count = sum(
            assignment.status == CourseAssignment.Status.OVERDUE
            for assignment in assignments
        )

        for assignment in assignments:
            assignment.display_percent = _assignment_progress(
                assignment,
                submission_by_course,
            )

        active_assignments = [
            assignment
            for assignment in assignments
            if assignment.status != CourseAssignment.Status.COMPLETED
        ][:4]
        upcoming_assignments = [
            assignment
            for assignment in assignments
            if assignment.status != CourseAssignment.Status.COMPLETED
        ][:4]

        average_result = (
            Submission.objects.filter(user=user)
            .aggregate(value=Avg('percent'))['value']
            or 0
        )

        context.update(
            {
                'assigned_courses_count': assigned_count,
                'completed_courses_count': completed_count,
                'overdue_courses_count': overdue_count,
                'completion_percent': (
                    round(completed_count / assigned_count * 100)
                    if assigned_count
                    else 0
                ),
                'average_result': round(average_result),
                'passed_tests_count': sum(item.passed for item in submissions),
                'active_assignments': active_assignments,
                'upcoming_assignments': upcoming_assignments,
                'recent_submissions': submissions[:5],
                'today': timezone.localdate(),
            }
        )

    return render(request, 'core/home.html', context)


@login_required
def help_page(request):
    return render(
        request,
        'core/help.html',
        {
            'breadcrumbs': breadcrumbs(
                ('Главная', '/'),
                ('Справка', None),
            ),
        },
    )
