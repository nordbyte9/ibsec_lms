# Integration Plan

## CSV import workflow

The `import_org_csv` management command imports organization data from a CSV file with the following columns:

- `username`
- `email`
- `first_name`
- `last_name`
- `department`
- `position`
- `role`

Import behavior:

- creates or updates users;
- creates missing departments and positions;
- updates the related `Profile`;
- writes an `IntegrationSyncLog` record with counts and status;
- marks the sync as failed if any row or file-level error occurs.

Recommended CSV editing workflow:

- edit the file in VS Code, or
- import it into Excel via `Data → From Text/CSV`, choose `UTF-8`, and use comma as the delimiter.

## LDAP / Active Directory roadmap

The project includes placeholder functions in `integrations/ldap.py`:

- `sync_from_ldap()`
- `sync_from_active_directory()`

Planned input fields:

- username / login;
- email;
- first name;
- last name;
- department;
- position / title;
- role mapping for `employee`, `security_officer`, and `admin`.

## Why this matters

Directory synchronization can keep the corporate structure up to date without manual maintenance. That makes it possible to:

- assign mandatory training by department or position;
- keep role mappings aligned with corporate HR data;
- reduce manual errors in user provisioning;
- provide a traceable import history via `IntegrationSyncLog`.
