import csv

from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render

from accounts.models import Department, Profile
from assignments.models import CourseAssignment
from audit.services import log_action
from courses.models import Course
from core.navigation import breadcrumbs
from quizzes.models import Submission


def _is_security_officer_or_admin(user):
    return user.is_authenticated and user.profile.role in ('security_officer', 'admin')


def _require_report_access(request):
    if not _is_security_officer_or_admin(request.user):
        return HttpResponseForbidden('Недостаточно прав')
    return None


def _base_filters(request):
    department_id = request.GET.get('department')
    course_id = request.GET.get('course')
    status = request.GET.get('status')
    return department_id, course_id, status


def _apply_assignment_filters(queryset, department_id=None, course_id=None, status=None):
    if department_id:
        queryset = queryset.filter(employee__profile__department_id=department_id)
    if course_id:
        queryset = queryset.filter(course_id=course_id)
    if status:
        queryset = queryset.filter(status=status)
    return queryset


def _export_csv(filename, headers, rows):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return response


def _log_csv_export(request, report_name, description):
    log_action(
        request.user,
        'csv_export',
        'Report',
        report_name,
        description,
        request=request,
    )


def _dashboard_breadcrumbs():
    return breadcrumbs(('Главная', '/'), ('Отчеты', None))


def _my_progress_breadcrumbs():
    return breadcrumbs(('Главная', '/'), ('Мой прогресс', None))


def _employee_report_breadcrumbs():
    return breadcrumbs(('Главная', '/'), ('Отчеты', '/reports/'), ('По сотрудникам', None))


def _department_report_breadcrumbs():
    return breadcrumbs(('Главная', '/'), ('Отчеты', '/reports/'), ('По подразделениям', None))


def _course_report_breadcrumbs():
    return breadcrumbs(('Главная', '/'), ('Отчеты', '/reports/'), ('По курсам', None))


@login_required
def dashboard(request):
    forbidden = _require_report_access(request)
    if forbidden:
        return forbidden

    department_id, course_id, status = _base_filters(request)
    assignments = _apply_assignment_filters(
        CourseAssignment.objects.select_related(
            'employee', 'employee__profile', 'employee__profile__department', 'course'
        ),
        department_id,
        course_id,
        status,
    )
    submissions = Submission.objects.select_related('quiz', 'quiz__course', 'user').all()
    if department_id:
        submissions = submissions.filter(user__profile__department_id=department_id)
    if course_id:
        submissions = submissions.filter(quiz__course_id=course_id)

    dashboard_data = {
        'employees_total': Profile.objects.filter(role='employee').count(),
        'assignments_total': assignments.count(),
        'completed_total': assignments.filter(status=CourseAssignment.Status.COMPLETED).count(),
        'overdue_total': assignments.filter(status=CourseAssignment.Status.OVERDUE).count(),
        'avg_percent': round(submissions.aggregate(avg=Avg('percent'))['avg'] or 0.0, 2),
    }
    departments = Department.objects.order_by('name')
    courses = Course.objects.order_by('title')
    return render(
        request,
        'reports/dashboard.html',
        {
            'dashboard': dashboard_data,
            'departments': departments,
            'courses': courses,
            'selected_department': department_id or '',
            'selected_course': course_id or '',
            'selected_status': status or '',
            'breadcrumbs': _dashboard_breadcrumbs(),
        },
    )


@login_required
def employee_report(request):
    forbidden = _require_report_access(request)
    if forbidden:
        return forbidden

    department_id, course_id, status = _base_filters(request)
    assignments = _apply_assignment_filters(
        CourseAssignment.objects.select_related(
            'employee',
            'employee__profile',
            'employee__profile__department',
            'employee__profile__position',
            'course',
        ),
        department_id,
        course_id,
        status,
    )
    rows = []
    employees = (
        Profile.objects.filter(role='employee')
        .select_related('user', 'department', 'position')
        .order_by('user__last_name', 'user__first_name', 'user__username')
    )
    if department_id:
        employees = employees.filter(department_id=department_id)

    for profile in employees:
        employee_assignments = assignments.filter(employee=profile.user)
        rows.append(
            {
                'employee': profile.user.get_full_name() or profile.user.username,
                'department': profile.department.name if profile.department else '-',
                'position': profile.position.name if profile.position else '-',
                'assigned': employee_assignments.count(),
                'completed': employee_assignments.filter(
                    status=CourseAssignment.Status.COMPLETED
                ).count(),
                'overdue': employee_assignments.filter(
                    status=CourseAssignment.Status.OVERDUE
                ).count(),
            }
        )

    return render(
        request,
        'reports/employee_report.html',
        {
            'rows': rows,
            'departments': Department.objects.order_by('name'),
            'courses': Course.objects.order_by('title'),
            'selected_department': department_id or '',
            'selected_course': course_id or '',
            'selected_status': status or '',
            'breadcrumbs': _employee_report_breadcrumbs(),
        },
    )


@login_required
def department_report(request):
    forbidden = _require_report_access(request)
    if forbidden:
        return forbidden

    department_id, course_id, status = _base_filters(request)
    assignments = _apply_assignment_filters(
        CourseAssignment.objects.select_related(
            'employee', 'employee__profile', 'employee__profile__department', 'course'
        ),
        department_id,
        course_id,
        status,
    )
    rows = []
    departments = Department.objects.order_by('name')
    if department_id:
        departments = departments.filter(id=department_id)

    for department in departments:
        department_assignments = assignments.filter(employee__profile__department=department)
        rows.append(
            {
                'department': department.name,
                'employees_total': Profile.objects.filter(
                    role='employee', department=department
                ).count(),
                'assigned': department_assignments.count(),
                'completed': department_assignments.filter(
                    status=CourseAssignment.Status.COMPLETED
                ).count(),
                'overdue': department_assignments.filter(
                    status=CourseAssignment.Status.OVERDUE
                ).count(),
            }
        )

    return render(
        request,
        'reports/department_report.html',
        {
            'rows': rows,
            'departments': Department.objects.order_by('name'),
            'courses': Course.objects.order_by('title'),
            'selected_department': department_id or '',
            'selected_course': course_id or '',
            'selected_status': status or '',
            'breadcrumbs': _department_report_breadcrumbs(),
        },
    )


@login_required
def course_report(request):
    forbidden = _require_report_access(request)
    if forbidden:
        return forbidden

    department_id, course_id, status = _base_filters(request)
    assignments = _apply_assignment_filters(
        CourseAssignment.objects.select_related(
            'employee',
            'employee__profile',
            'employee__profile__department',
            'course',
            'course__training_program',
        ),
        department_id,
        course_id,
        status,
    )
    submissions = Submission.objects.select_related('quiz', 'quiz__course', 'user').all()
    if department_id:
        submissions = submissions.filter(user__profile__department_id=department_id)
    if course_id:
        submissions = submissions.filter(quiz__course_id=course_id)

    rows = []
    courses = Course.objects.select_related('training_program').order_by('title')
    if course_id:
        courses = courses.filter(id=course_id)

    for course in courses:
        course_assignments = assignments.filter(course=course)
        course_submissions = submissions.filter(quiz__course=course)
        rows.append(
            {
                'course': course.title,
                'program': course.training_program.title if course.training_program else '-',
                'assigned': course_assignments.count(),
                'completed': course_assignments.filter(
                    status=CourseAssignment.Status.COMPLETED
                ).count(),
                'avg_percent': round(
                    course_submissions.aggregate(avg=Avg('percent'))['avg'] or 0.0,
                    2,
                ),
            }
        )

    return render(
        request,
        'reports/course_report.html',
        {
            'rows': rows,
            'departments': Department.objects.order_by('name'),
            'courses': Course.objects.order_by('title'),
            'selected_department': department_id or '',
            'selected_course': course_id or '',
            'selected_status': status or '',
            'breadcrumbs': _course_report_breadcrumbs(),
        },
    )


@login_required
def export_employee_csv(request):
    forbidden = _require_report_access(request)
    if forbidden:
        return forbidden

    department_id, course_id, status = _base_filters(request)
    assignments = _apply_assignment_filters(
        CourseAssignment.objects.select_related(
            'employee',
            'employee__profile',
            'employee__profile__department',
            'employee__profile__position',
            'course',
        ),
        department_id,
        course_id,
        status,
    )
    employees = (
        Profile.objects.filter(role='employee')
        .select_related('user', 'department', 'position')
        .order_by('user__username')
    )
    if department_id:
        employees = employees.filter(department_id=department_id)

    rows = []
    for profile in employees:
        employee_assignments = assignments.filter(employee=profile.user)
        rows.append(
            [
                profile.user.get_full_name() or profile.user.username,
                profile.department.name if profile.department else '',
                profile.position.name if profile.position else '',
                employee_assignments.count(),
                employee_assignments.filter(status=CourseAssignment.Status.COMPLETED).count(),
                employee_assignments.filter(status=CourseAssignment.Status.OVERDUE).count(),
            ]
        )

    _log_csv_export(request, 'employee_report', 'Экспорт CSV отчета по сотрудникам')
    return _export_csv(
        'employee_report.csv',
        ['Сотрудник', 'Подразделение', 'Должность', 'Назначено', 'Завершено', 'Просрочено'],
        rows,
    )


@login_required
def export_department_csv(request):
    forbidden = _require_report_access(request)
    if forbidden:
        return forbidden

    department_id, course_id, status = _base_filters(request)
    assignments = _apply_assignment_filters(
        CourseAssignment.objects.select_related(
            'employee', 'employee__profile', 'employee__profile__department', 'course'
        ),
        department_id,
        course_id,
        status,
    )
    departments = Department.objects.order_by('name')
    if department_id:
        departments = departments.filter(id=department_id)

    rows = []
    for department in departments:
        department_assignments = assignments.filter(employee__profile__department=department)
        rows.append(
            [
                department.name,
                Profile.objects.filter(role='employee', department=department).count(),
                department_assignments.count(),
                department_assignments.filter(status=CourseAssignment.Status.COMPLETED).count(),
                department_assignments.filter(status=CourseAssignment.Status.OVERDUE).count(),
            ]
        )

    _log_csv_export(request, 'department_report', 'Экспорт CSV отчета по подразделениям')
    return _export_csv(
        'department_report.csv',
        ['Подразделение', 'Всего сотрудников', 'Назначений', 'Завершено', 'Просрочено'],
        rows,
    )


@login_required
def export_course_csv(request):
    forbidden = _require_report_access(request)
    if forbidden:
        return forbidden

    department_id, course_id, status = _base_filters(request)
    assignments = _apply_assignment_filters(
        CourseAssignment.objects.select_related(
            'employee',
            'employee__profile',
            'employee__profile__department',
            'course',
            'course__training_program',
        ),
        department_id,
        course_id,
        status,
    )
    submissions = Submission.objects.select_related('quiz', 'quiz__course', 'user').all()
    if department_id:
        submissions = submissions.filter(user__profile__department_id=department_id)
    if course_id:
        submissions = submissions.filter(quiz__course_id=course_id)

    courses = Course.objects.select_related('training_program').order_by('title')
    if course_id:
        courses = courses.filter(id=course_id)

    rows = []
    for course in courses:
        course_assignments = assignments.filter(course=course)
        course_submissions = submissions.filter(quiz__course=course)
        rows.append(
            [
                course.title,
                course.training_program.title if course.training_program else '',
                course_assignments.count(),
                course_assignments.filter(status=CourseAssignment.Status.COMPLETED).count(),
                round(
                    course_submissions.aggregate(avg=Avg('percent'))['avg'] or 0.0,
                    2,
                ),
            ]
        )

    _log_csv_export(request, 'course_report', 'Экспорт CSV отчета по курсам')
    return _export_csv(
        'course_report.csv',
        ['Курс', 'Программа ИБ', 'Назначено', 'Завершено', 'Средний результат, %'],
        rows,
    )


@login_required
def my_progress(request):
    submissions = (
        Submission.objects.filter(user=request.user)
        .select_related('quiz')
        .order_by('-taken_at')
    )
    return render(
        request,
        'reports/my_progress.html',
        {'submissions': submissions, 'breadcrumbs': _my_progress_breadcrumbs()},
    )


@login_required
def analytics(request):
    return dashboard(request)


@login_required
def export_csv(request):
    return export_course_csv(request)
