import csv
from collections import Counter

from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render

from accounts.models import Department, Profile
from accounts.permissions import Permission, has_permission
from assignments.models import CourseAssignment
from audit.services import log_action
from courses.models import Course
from core.navigation import breadcrumbs
from quizzes.models import Submission


def _require_report_access(request):
    if not has_permission(request.user, Permission.VIEW_REPORTS):
        return HttpResponseForbidden('Недостаточно прав')
    return None


def _base_filters(request):
    department_id = request.GET.get('department', '').strip()
    course_id = request.GET.get('course', '').strip()
    status = request.GET.get('status', '').strip()
    return department_id, course_id, status


def _apply_assignment_filters(queryset, department_id=None, course_id=None, status=None):
    if department_id:
        queryset = queryset.filter(employee__profile__department_id=department_id)
    if course_id:
        queryset = queryset.filter(course_id=course_id)
    valid_statuses = {value for value, _ in CourseAssignment.Status.choices}
    if status in valid_statuses:
        queryset = queryset.filter(status=status)
    return queryset


def _apply_submission_filters(queryset, department_id=None, course_id=None):
    if department_id:
        queryset = queryset.filter(user__profile__department_id=department_id)
    if course_id:
        queryset = queryset.filter(quiz__course_id=course_id)
    return queryset


def _export_csv(filename, headers, rows):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows(rows)
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
    return breadcrumbs(('Главная', '/'), ('Отчёты', None))


def _my_progress_breadcrumbs():
    return breadcrumbs(('Главная', '/'), ('Мой прогресс', None))


def _employee_report_breadcrumbs():
    return breadcrumbs(('Главная', '/'), ('Отчёты', '/reports/'), ('По сотрудникам', None))


def _department_report_breadcrumbs():
    return breadcrumbs(('Главная', '/'), ('Отчёты', '/reports/'), ('По подразделениям', None))


def _course_report_breadcrumbs():
    return breadcrumbs(('Главная', '/'), ('Отчёты', '/reports/'), ('По курсам', None))


def _percent(part, whole):
    return round((part / whole) * 100, 1) if whole else 0


def _dashboard_context(request):
    department_id, course_id, status = _base_filters(request)

    assignments = _apply_assignment_filters(
        CourseAssignment.objects.select_related(
            'employee',
            'employee__profile',
            'employee__profile__department',
            'course',
        ),
        department_id,
        course_id,
        status,
    )
    submissions = _apply_submission_filters(
        Submission.objects.select_related('quiz', 'quiz__course', 'user'),
        department_id,
        course_id,
    )

    assignments_total = assignments.count()
    completed_total = assignments.filter(status=CourseAssignment.Status.COMPLETED).count()
    overdue_total = assignments.filter(status=CourseAssignment.Status.OVERDUE).count()
    in_progress_total = assignments.filter(status=CourseAssignment.Status.IN_PROGRESS).count()
    assigned_total = assignments.filter(status=CourseAssignment.Status.ASSIGNED).count()
    avg_percent = round(submissions.aggregate(avg=Avg('percent'))['avg'] or 0.0, 1)
    passed_total = submissions.filter(passed=True).count()
    submissions_total = submissions.count()

    status_items = [
        {'label': 'Завершено', 'value': completed_total, 'percent': _percent(completed_total, assignments_total), 'kind': 'success'},
        {'label': 'В процессе', 'value': in_progress_total, 'percent': _percent(in_progress_total, assignments_total), 'kind': 'primary'},
        {'label': 'Назначено', 'value': assigned_total, 'percent': _percent(assigned_total, assignments_total), 'kind': 'muted'},
        {'label': 'Просрочено', 'value': overdue_total, 'percent': _percent(overdue_total, assignments_total), 'kind': 'danger'},
    ]

    department_rows = []
    departments = Department.objects.order_by('name')
    if department_id:
        departments = departments.filter(pk=department_id)
    for department in departments:
        department_assignments = assignments.filter(employee__profile__department=department)
        total = department_assignments.count()
        completed = department_assignments.filter(status=CourseAssignment.Status.COMPLETED).count()
        department_submissions = submissions.filter(user__profile__department=department)
        department_rows.append({
            'name': department.name,
            'assigned': total,
            'completed': completed,
            'completion_percent': _percent(completed, total),
            'avg_percent': round(department_submissions.aggregate(avg=Avg('percent'))['avg'] or 0.0, 1),
        })
    department_rows.sort(key=lambda item: (-item['completion_percent'], item['name']))

    course_rows = []
    courses_query = Course.objects.order_by('title')
    if course_id:
        courses_query = courses_query.filter(pk=course_id)
    for course in courses_query:
        course_assignments = assignments.filter(course=course)
        total = course_assignments.count()
        if not total and (department_id or status):
            continue
        completed = course_assignments.filter(status=CourseAssignment.Status.COMPLETED).count()
        overdue = course_assignments.filter(status=CourseAssignment.Status.OVERDUE).count()
        course_submissions = submissions.filter(quiz__course=course)
        course_rows.append({
            'course': course,
            'assigned': total,
            'completed': completed,
            'overdue': overdue,
            'completion_percent': _percent(completed, total),
            'avg_percent': round(course_submissions.aggregate(avg=Avg('percent'))['avg'] or 0.0, 1),
        })
    course_rows.sort(key=lambda item: (-item['assigned'], item['course'].title))

    recent_results = list(
        submissions.order_by('-taken_at', '-id')[:8]
    )

    overdue_courses_counter = Counter(
        assignments.filter(status=CourseAssignment.Status.OVERDUE)
        .values_list('course__title', flat=True)
    )
    overdue_courses = [
        {'title': title, 'count': count}
        for title, count in overdue_courses_counter.most_common(5)
    ]

    dashboard_data = {
        'employees_total': Profile.objects.filter(role=Profile.Role.EMPLOYEE).count(),
        'assignments_total': assignments_total,
        'completed_total': completed_total,
        'overdue_total': overdue_total,
        'avg_percent': avg_percent,
        'completion_percent': _percent(completed_total, assignments_total),
        'pass_percent': _percent(passed_total, submissions_total),
        'passed_total': passed_total,
        'failed_total': max(submissions_total - passed_total, 0),
        'submissions_total': submissions_total,
    }

    return {
        'dashboard': dashboard_data,
        'status_items': status_items,
        'department_rows': department_rows[:8],
        'course_rows': course_rows[:8],
        'recent_results': recent_results,
        'overdue_courses': overdue_courses,
        'departments': Department.objects.order_by('name'),
        'courses': Course.objects.order_by('title'),
        'selected_department': department_id,
        'selected_course': course_id,
        'selected_status': status,
        'can_export_reports': has_permission(request.user, Permission.EXPORT_REPORTS),
        'breadcrumbs': _dashboard_breadcrumbs(),
    }


@login_required
def dashboard(request):
    forbidden = _require_report_access(request)
    if forbidden:
        return forbidden
    return render(request, 'reports/dashboard.html', _dashboard_context(request))


@login_required
def employee_report(request):
    forbidden = _require_report_access(request)
    if forbidden:
        return forbidden
    department_id, course_id, status = _base_filters(request)
    assignments = _apply_assignment_filters(
        CourseAssignment.objects.select_related(
            'employee', 'employee__profile', 'employee__profile__department',
            'employee__profile__position', 'course',
        ), department_id, course_id, status,
    )
    employees = Profile.objects.filter(role=Profile.Role.EMPLOYEE).select_related(
        'user', 'department', 'position'
    ).order_by('user__last_name', 'user__first_name', 'user__username')
    if department_id:
        employees = employees.filter(department_id=department_id)
    rows = []
    for profile in employees:
        employee_assignments = assignments.filter(employee=profile.user)
        rows.append({
            'employee': profile.user.get_full_name() or profile.user.username,
            'department': profile.department.name if profile.department else '—',
            'position': profile.position.name if profile.position else '—',
            'assigned': employee_assignments.count(),
            'completed': employee_assignments.filter(status=CourseAssignment.Status.COMPLETED).count(),
            'overdue': employee_assignments.filter(status=CourseAssignment.Status.OVERDUE).count(),
        })
    return render(request, 'reports/employee_report.html', {
        'rows': rows,
        'departments': Department.objects.order_by('name'),
        'courses': Course.objects.order_by('title'),
        'selected_department': department_id,
        'selected_course': course_id,
        'selected_status': status,
        'breadcrumbs': _employee_report_breadcrumbs(),
    })


@login_required
def department_report(request):
    forbidden = _require_report_access(request)
    if forbidden:
        return forbidden
    department_id, course_id, status = _base_filters(request)
    assignments = _apply_assignment_filters(
        CourseAssignment.objects.select_related(
            'employee', 'employee__profile', 'employee__profile__department', 'course'
        ), department_id, course_id, status,
    )
    departments = Department.objects.order_by('name')
    if department_id:
        departments = departments.filter(id=department_id)
    rows = []
    for department in departments:
        department_assignments = assignments.filter(employee__profile__department=department)
        rows.append({
            'department': department.name,
            'employees_total': Profile.objects.filter(role=Profile.Role.EMPLOYEE, department=department).count(),
            'assigned': department_assignments.count(),
            'completed': department_assignments.filter(status=CourseAssignment.Status.COMPLETED).count(),
            'overdue': department_assignments.filter(status=CourseAssignment.Status.OVERDUE).count(),
        })
    return render(request, 'reports/department_report.html', {
        'rows': rows,
        'departments': Department.objects.order_by('name'),
        'courses': Course.objects.order_by('title'),
        'selected_department': department_id,
        'selected_course': course_id,
        'selected_status': status,
        'breadcrumbs': _department_report_breadcrumbs(),
    })


@login_required
def course_report(request):
    forbidden = _require_report_access(request)
    if forbidden:
        return forbidden
    department_id, course_id, status = _base_filters(request)
    assignments = _apply_assignment_filters(
        CourseAssignment.objects.select_related(
            'employee', 'employee__profile', 'employee__profile__department',
            'course', 'course__training_program',
        ), department_id, course_id, status,
    )
    submissions = _apply_submission_filters(
        Submission.objects.select_related('quiz', 'quiz__course', 'user'),
        department_id, course_id,
    )
    courses = Course.objects.select_related('training_program').order_by('title')
    if course_id:
        courses = courses.filter(id=course_id)
    rows = []
    for course in courses:
        course_assignments = assignments.filter(course=course)
        course_submissions = submissions.filter(quiz__course=course)
        rows.append({
            'course': course.title,
            'program': course.training_program.title if course.training_program else '—',
            'assigned': course_assignments.count(),
            'completed': course_assignments.filter(status=CourseAssignment.Status.COMPLETED).count(),
            'avg_percent': round(course_submissions.aggregate(avg=Avg('percent'))['avg'] or 0.0, 1),
        })
    return render(request, 'reports/course_report.html', {
        'rows': rows,
        'departments': Department.objects.order_by('name'),
        'courses': Course.objects.order_by('title'),
        'selected_department': department_id,
        'selected_course': course_id,
        'selected_status': status,
        'breadcrumbs': _course_report_breadcrumbs(),
    })


@login_required
def export_employee_csv(request):
    if not has_permission(request.user, Permission.EXPORT_REPORTS):
        return HttpResponseForbidden('Недостаточно прав')
    department_id, course_id, status = _base_filters(request)
    assignments = _apply_assignment_filters(
        CourseAssignment.objects.select_related(
            'employee', 'employee__profile', 'employee__profile__department',
            'employee__profile__position', 'course',
        ), department_id, course_id, status,
    )
    employees = Profile.objects.filter(role=Profile.Role.EMPLOYEE).select_related(
        'user', 'department', 'position'
    ).order_by('user__username')
    if department_id:
        employees = employees.filter(department_id=department_id)
    rows = []
    for profile in employees:
        employee_assignments = assignments.filter(employee=profile.user)
        rows.append([
            profile.user.get_full_name() or profile.user.username,
            profile.department.name if profile.department else '',
            profile.position.name if profile.position else '',
            employee_assignments.count(),
            employee_assignments.filter(status=CourseAssignment.Status.COMPLETED).count(),
            employee_assignments.filter(status=CourseAssignment.Status.OVERDUE).count(),
        ])
    _log_csv_export(request, 'employee_report', 'Экспорт отчёта по сотрудникам')
    return _export_csv('employee_report.csv', [
        'Сотрудник', 'Подразделение', 'Должность', 'Назначено', 'Завершено', 'Просрочено'
    ], rows)


@login_required
def export_department_csv(request):
    if not has_permission(request.user, Permission.EXPORT_REPORTS):
        return HttpResponseForbidden('Недостаточно прав')
    department_id, course_id, status = _base_filters(request)
    assignments = _apply_assignment_filters(
        CourseAssignment.objects.select_related(
            'employee', 'employee__profile', 'employee__profile__department', 'course'
        ), department_id, course_id, status,
    )
    departments = Department.objects.order_by('name')
    if department_id:
        departments = departments.filter(id=department_id)
    rows = []
    for department in departments:
        department_assignments = assignments.filter(employee__profile__department=department)
        rows.append([
            department.name,
            Profile.objects.filter(role=Profile.Role.EMPLOYEE, department=department).count(),
            department_assignments.count(),
            department_assignments.filter(status=CourseAssignment.Status.COMPLETED).count(),
            department_assignments.filter(status=CourseAssignment.Status.OVERDUE).count(),
        ])
    _log_csv_export(request, 'department_report', 'Экспорт отчёта по подразделениям')
    return _export_csv('department_report.csv', [
        'Подразделение', 'Всего сотрудников', 'Назначений', 'Завершено', 'Просрочено'
    ], rows)


@login_required
def export_course_csv(request):
    if not has_permission(request.user, Permission.EXPORT_REPORTS):
        return HttpResponseForbidden('Недостаточно прав')
    department_id, course_id, status = _base_filters(request)
    assignments = _apply_assignment_filters(
        CourseAssignment.objects.select_related(
            'employee', 'employee__profile', 'employee__profile__department',
            'course', 'course__training_program',
        ), department_id, course_id, status,
    )
    submissions = _apply_submission_filters(
        Submission.objects.select_related('quiz', 'quiz__course', 'user'),
        department_id, course_id,
    )
    courses = Course.objects.select_related('training_program').order_by('title')
    if course_id:
        courses = courses.filter(id=course_id)
    rows = []
    for course in courses:
        course_assignments = assignments.filter(course=course)
        course_submissions = submissions.filter(quiz__course=course)
        rows.append([
            course.title,
            course.training_program.title if course.training_program else '',
            course_assignments.count(),
            course_assignments.filter(status=CourseAssignment.Status.COMPLETED).count(),
            round(course_submissions.aggregate(avg=Avg('percent'))['avg'] or 0.0, 1),
        ])
    _log_csv_export(request, 'course_report', 'Экспорт отчёта по курсам')
    return _export_csv('course_report.csv', [
        'Курс', 'Программа ИБ', 'Назначено', 'Завершено', 'Средний результат, %'
    ], rows)


@login_required
def my_progress(request):
    submissions = Submission.objects.filter(user=request.user).select_related('quiz').order_by('-taken_at')
    return render(request, 'reports/my_progress.html', {
        'submissions': submissions,
        'breadcrumbs': _my_progress_breadcrumbs(),
    })


@login_required
def analytics(request):
    return dashboard(request)


@login_required
def export_csv(request):
    return export_course_csv(request)
