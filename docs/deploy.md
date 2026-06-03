# Deploy Guide

## Local run

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in values.
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Prepare `.env`

Required variables:

- `SECRET_KEY` — a strong random value;
- `DEBUG` — `False` for production;
- `ALLOWED_HOSTS` — comma-separated hostnames;
- `CSRF_TRUSTED_ORIGINS` — comma-separated trusted HTTPS origins.

Example:

```env
SECRET_KEY=replace-with-a-long-random-secret
DEBUG=False
ALLOWED_HOSTS=ibsec.example.com,www.ibsec.example.com
CSRF_TRUSTED_ORIGINS=https://ibsec.example.com,https://www.ibsec.example.com
```

## Migrations

Apply schema changes before the first launch:

```bash
python manage.py migrate
```

## Static files

Collect static assets into `STATIC_ROOT`:

```bash
python manage.py collectstatic --noinput
```

## Superuser

Create an administrative account if it does not exist:

```bash
python manage.py createsuperuser
```

## Run on hosting

Typical deployment flow:

1. Set environment variables on the host.
2. Run migrations.
3. Run `collectstatic`.
4. Start the WSGI/ASGI application server.
5. Put a reverse proxy in front of Django if needed.

## Post-deploy checks

- open the site and verify the login page;
- verify `/admin/` access with a superuser;
- check course catalog, assignments, quizzes, reports, audit, and integrations pages;
- confirm static assets load correctly;
- ensure `DEBUG=False` and `ALLOWED_HOSTS` match the host.
