from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render

from .forms import CourseAssignmentForm
from .models import CourseAssignment


def _can_manage_assignments(user):
    return user.is_authenticated and user.profile.role in ('security_officer', 'admin')


@login_required
def my_assignments(request):
    assignments = (
        CourseAssignment.objects.filter(employee=request.user)
        .select_related('course', 'assigned_by', 'employee', 'course__training_program', 'course__training_program__category')
        .order_by('-assigned_at')
    )
    return render(request, 'assignments/my_assignments.html', {'assignments': assignments})


@login_required
def assignment_list(request):
    if not _can_manage_assignments(request.user):
        return HttpResponseForbidden('Недостаточно прав')
    assignments = (
        CourseAssignment.objects.select_related('course', 'assigned_by', 'employee', 'course__training_program', 'course__training_program__category')
        .order_by('-assigned_at')
    )
    status = request.GET.get('status')
    if status:
        assignments = assignments.filter(status=status)
    return render(
        request,
        'assignments/assignment_list.html',
        {'assignments': assignments, 'status': status or ''},
    )


@login_required
def assignment_create(request):
    if not _can_manage_assignments(request.user):
        return HttpResponseForbidden('Недостаточно прав')
    if request.method == 'POST':
        form = CourseAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.assigned_by = request.user
            assignment.status = CourseAssignment.Status.ASSIGNED
            assignment.save()
            return redirect('assignments:list')
    else:
        form = CourseAssignmentForm()
    return render(request, 'assignments/assignment_form.html', {'form': form})
