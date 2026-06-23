#!/bin/sh
set -eu

is_true() {
    normalized_value="$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]')"
    case "$normalized_value" in
        1|true|yes|on) return 0 ;;
        *) return 1 ;;
    esac
}

echo "Running Django system checks..."
python manage.py check

if is_true "${RUN_MIGRATIONS:-true}"; then
    echo "Applying database migrations..."
    python manage.py migrate --noinput
    echo "Verifying that no migrations remain unapplied..."
    python manage.py migrate --check
else
    echo "Database migrations are disabled by RUN_MIGRATIONS=${RUN_MIGRATIONS:-}."
fi

if is_true "${COLLECT_STATIC:-true}"; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
else
    echo "Static collection is disabled by COLLECT_STATIC=${COLLECT_STATIC:-}."
fi

exec "$@"
