# Requirements Mapping

| Requirement of practice | Implemented in project |
|---|---|
| Django/Python stack | Django 4.2.13 on Python 3, with Django ORM and template-based UI |
| SQL database | SQLite by default, PostgreSQL supported via settings |
| Three user roles | `employee`, `security_officer`, `admin` |
| Personal account | Profile page, personal assignments, personal progress, personal quiz history |
| Admin panel | Django admin with domain models registered |
| Mandatory training assignments | `assignments` app with course assignment lifecycle |
| Testing / quiz control | `quizzes` app with attempts, scores, pass threshold, and limits |
| Reporting | `reports` app with dashboard and CSV exports |
| Audit log | `audit` app with action logging and audit journal page |
| CSV / LDAP / AD integrations | `integrations` app with CSV import command and LDAP/AD placeholders |
| Deploy documentation | `docs/deploy.md`, `.env.example`, static/media production settings |
| Tests | Django test suite covering access, audit, integration import, and core flows |

## Expanded mapping

| Practice item | Functional coverage |
|---|---|
| User management | Roles, profile, department, position, authentication, and access control |
| Corporate structure | Departments and positions stored as separate models and used in reports and imports |
| Mandatory learning | Training programs, course targeting, assignments, deadlines, and completion tracking |
| Control and supervision | Dashboard, employee/dept/course reports, CSV export, and audit journal |
| External data loading | CSV org-structure import and future LDAP/AD integration scaffold |
| Production readiness | Env-driven settings, `collectstatic`, deploy guide, release checklist |
| Quality assurance | Smoke checklist and automated Django tests |

