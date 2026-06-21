#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

docker compose --env-file .env.docker ps
curl --fail http://localhost:8000/health/
echo
docker compose --env-file .env.docker exec -T db \
    psql -U ibsec_user -d ibsec_lms -c "SELECT version();"
docker compose --env-file .env.docker exec -T web \
    python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print(connection.vendor); print(connection.settings_dict['NAME'])"
docker compose --env-file .env.docker exec -T web \
    python manage.py shell -c "from django.contrib.auth.models import User; from courses.models import Course; from quizzes.models import Quiz; print('users=', User.objects.count()); print('courses=', Course.objects.count()); print('quizzes=', Quiz.objects.count())"
