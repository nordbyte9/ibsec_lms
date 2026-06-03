# User Roles

## `employee`

### Rights

- view assigned courses;
- open course materials;
- take quizzes;
- view personal results and progress;
- view personal assignments and attempt history.

### Accessible pages

- homepage;
- course catalog;
- personal assignments;
- course detail;
- quiz pages;
- quiz result page;
- personal progress page;
- profile page.

## `security_officer`

### Rights

- everything available to `employee`;
- create and manage assignments;
- view reports and dashboards;
- view audit journal;
- view integration status page;
- review CSV import history;
- create and manage courses in the current project scope.

### Accessible pages

- homepage;
- course catalog;
- personal assignments;
- all assignments;
- reports dashboard;
- employee report;
- department report;
- course report;
- audit journal;
- integrations page;
- profile page;
- admin panel if granted staff permissions.

## `admin`

### Rights

- everything available to `security_officer`;
- full Django admin access;
- operational management of the system;
- review of all reports, logs, and integration records.

### Accessible pages

- all pages available to `security_officer`;
- Django admin `/admin/`;
- system configuration and model administration.

## Access model summary

- `employee` works only with personal data and learning flow.
- `security_officer` controls training execution and compliance reporting.
- `admin` has the broadest operational access and system administration rights.

