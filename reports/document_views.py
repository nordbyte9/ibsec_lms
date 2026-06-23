from __future__ import annotations

from collections import Counter
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.utils import timezone

from accounts.models import Department
from assignments.models import CourseAssignment
from audit.services import log_action
from courses.models import Course
from quizzes.models import Submission

from .document_exports import (
    CertificateData,
    DOCX_CONTENT_TYPE,
    XLSX_CONTENT_TYPE,
    build_certificate_docx,
    build_training_registry_xlsx,
)


def _role(user) -> str | None:
    profile = getattr(user, "profile", None)
    return getattr(profile, "role", None)


def _can_manage_reports(user) -> bool:
    return user.is_authenticated and (
        user.is_superuser or _role(user) in {"security_officer", "admin"}
    )


def _safe_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _filtered_assignments(request):
    queryset = CourseAssignment.objects.select_related(
        "employee",
        "employee__profile",
        "employee__profile__department",
        "employee__profile__position",
        "course",
        "course__training_program",
        "assigned_by",
    ).order_by("employee__last_name", "employee__first_name", "employee__username", "course__title")

    department_id = _safe_int(request.GET.get("department"))
    course_id = _safe_int(request.GET.get("course"))
    status = request.GET.get("status", "").strip()
    valid_statuses = {choice for choice, _ in CourseAssignment.Status.choices}

    if department_id:
        queryset = queryset.filter(employee__profile__department_id=department_id)
    if course_id:
        queryset = queryset.filter(course_id=course_id)
    if status in valid_statuses:
        queryset = queryset.filter(status=status)

    filter_parts = []
    if department_id:
        department_name = (
            Department.objects.filter(pk=department_id).values_list("name", flat=True).first()
        )
        filter_parts.append(f"подразделение={department_name or department_id}")
    if course_id:
        course_title = Course.objects.filter(pk=course_id).values_list("title", flat=True).first()
        filter_parts.append(f"курс={course_title or course_id}")
    if status in valid_statuses:
        filter_parts.append(f"статус={dict(CourseAssignment.Status.choices)[status]}")

    return queryset, "; ".join(filter_parts) if filter_parts else "Все данные"


def _submission_stats(assignments):
    pairs = {(item.employee_id, item.course_id) for item in assignments}
    if not pairs:
        return {}, Counter()

    user_ids = {user_id for user_id, _ in pairs}
    course_ids = {course_id for _, course_id in pairs}
    submissions = (
        Submission.objects.filter(user_id__in=user_ids, quiz__course_id__in=course_ids)
        .select_related("quiz")
        .order_by("-taken_at", "-id")
    )

    latest = {}
    attempts = Counter()
    for submission in submissions:
        key = (submission.user_id, submission.quiz.course_id)
        if key not in pairs:
            continue
        attempts[key] += 1
        latest.setdefault(key, submission)
    return latest, attempts


def _registry_rows(assignments):
    assignment_list = list(assignments)
    latest_submissions, attempts = _submission_stats(assignment_list)
    rows = []

    for assignment in assignment_list:
        profile = getattr(assignment.employee, "profile", None)
        department = getattr(getattr(profile, "department", None), "name", "")
        position = getattr(getattr(profile, "position", None), "name", "")
        program = getattr(assignment.course.training_program, "title", "") if assignment.course.training_program else ""
        key = (assignment.employee_id, assignment.course_id)
        latest = latest_submissions.get(key)
        valid_until = None
        if assignment.completed_at and assignment.course.validity_days:
            completed_local = timezone.localtime(assignment.completed_at) if timezone.is_aware(assignment.completed_at) else assignment.completed_at
            valid_until = completed_local.date() + timedelta(days=assignment.course.validity_days)

        rows.append(
            {
                "assignment_id": assignment.pk,
                "employee": assignment.employee.get_full_name() or assignment.employee.username,
                "username": assignment.employee.username,
                "department": department,
                "position": position,
                "course": assignment.course.title,
                "program": program,
                "status": assignment.get_status_display(),
                "assigned_at": assignment.assigned_at,
                "due_date": assignment.due_date,
                "completed_at": assignment.completed_at,
                "latest_percent": latest.percent if latest else None,
                "passed": "Да" if latest and latest.passed else ("Нет" if latest else "—"),
                "attempts": attempts.get(key, 0),
                "valid_until": valid_until,
            }
        )
    return rows


def _attachment_response(content: bytes, content_type: str, filename: str) -> HttpResponse:
    response = HttpResponse(content, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@login_required
def export_training_registry_xlsx(request):
    if not _can_manage_reports(request.user):
        return HttpResponseForbidden("Недостаточно прав")

    assignments, filters_description = _filtered_assignments(request)
    rows = _registry_rows(assignments)
    generated_at = timezone.now()
    content = build_training_registry_xlsx(
        rows,
        generated_at=generated_at,
        filters_description=filters_description,
    )

    log_action(
        request.user,
        "xlsx_export",
        "Report",
        "training_registry",
        f"Экспортирован XLSX-реестр обучения: {len(rows)} записей; {filters_description}",
        request=request,
    )
    filename = f"training_registry_{timezone.localdate():%Y-%m-%d}.xlsx"
    return _attachment_response(content, XLSX_CONTENT_TYPE, filename)


@login_required
def download_assignment_certificate_docx(request, assignment_id: int):
    assignment = get_object_or_404(
        CourseAssignment.objects.select_related(
            "employee",
            "employee__profile",
            "employee__profile__department",
            "employee__profile__position",
            "course",
            "course__training_program",
        ),
        pk=assignment_id,
    )

    can_manage = _can_manage_reports(request.user)
    if assignment.employee_id != request.user.id and not can_manage:
        return HttpResponseForbidden("Недостаточно прав")
    if assignment.status != CourseAssignment.Status.COMPLETED or assignment.completed_at is None:
        return HttpResponseNotFound("Сертификат доступен только после завершения курса")

    submissions = Submission.objects.filter(
        user=assignment.employee,
        quiz__course=assignment.course,
    ).select_related("quiz")
    latest_submission = (
        submissions.filter(passed=True).order_by("-taken_at", "-id").first()
        or submissions.order_by("-taken_at", "-id").first()
    )
    profile = getattr(assignment.employee, "profile", None)
    department = getattr(getattr(profile, "department", None), "name", "")
    position = getattr(getattr(profile, "position", None), "name", "")
    completed_local = (
        timezone.localtime(assignment.completed_at)
        if timezone.is_aware(assignment.completed_at)
        else assignment.completed_at
    )
    valid_until = None
    if assignment.course.validity_days:
        valid_until = completed_local.date() + timedelta(days=assignment.course.validity_days)

    data = CertificateData(
        certificate_number=f"IBSEC-{assignment.pk:06d}",
        organization_name=getattr(settings, "DOCUMENT_ORGANIZATION_NAME", "IBSec LMS"),
        employee_name=assignment.employee.get_full_name() or assignment.employee.username,
        username=assignment.employee.username,
        department=department,
        position=position,
        course_title=assignment.course.title,
        program_title=(assignment.course.training_program.title if assignment.course.training_program else ""),
        completed_at=completed_local.date(),
        result_percent=(latest_submission.percent if latest_submission else None),
        valid_until=valid_until,
        signer_title=getattr(
            settings,
            "DOCUMENT_SIGNER_TITLE",
            "Ответственный за информационную безопасность",
        ),
        signer_name=getattr(settings, "DOCUMENT_SIGNER_NAME", ""),
    )
    content = build_certificate_docx(data)

    log_action(
        request.user,
        "docx_certificate",
        "CourseAssignment",
        assignment.pk,
        f"Сформирован DOCX-сертификат по курсу «{assignment.course.title}»",
        request=request,
    )
    filename = f"certificate_{assignment.pk}.docx"
    return _attachment_response(content, DOCX_CONTENT_TYPE, filename)
