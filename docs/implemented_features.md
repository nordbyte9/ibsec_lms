# Implemented Features

## Accounts

- Authentication, login, logout, profile editing.
- Roles: `employee`, `security_officer`, `admin`.
- Business value: ensures role-based access and separates learner, control, and administrative responsibilities.

## Corporate structure

- Models: `Department`, `Position`.
- Profiles link to department and position.
- Business value: supports training assignment by organizational context and accurate reporting.

## Courses

- Security categories and training programs.
- Courses with mandatory flag, validity, target departments, and target positions.
- Business value: defines corporate security training paths and relevance rules.

## Assignments

- Course assignment model and pages for personal and global views.
- Business value: automates scheduling of mandatory training and deadline control.

## Quizzes

- Quiz configuration with pass score, time limit, max attempts, and active state.
- Submission tracking with attempt history and completion updates.
- Business value: validates knowledge acquisition and stores training completion evidence.

## Reports

- Dashboard and reports by employee, department, and course.
- CSV export for reporting.
- Business value: gives the security owner and management a consolidated view of compliance status.

## Audit

- Audit log model and journal page.
- Logging for assignments, quiz submissions, completions, and CSV exports.
- Business value: improves accountability and supports investigation of sensitive actions.

## Integrations

- CSV import of org structure.
- LDAP / Active Directory placeholders.
- Business value: reduces manual maintenance and prepares synchronization with corporate directories.

## Deployment support

- Production settings via environment variables.
- `STATIC_ROOT`, `MEDIA_ROOT`, `.env.example`, deploy guide, and release checklist.
- Business value: makes the project ready for hosting and production rollout.

## Documentation and QA

- Smoke checklist, demo scenario, release checklist, and practice mapping.
- Django test coverage for core behavior.
- Business value: simplifies acceptance, demonstration, and regression control.

