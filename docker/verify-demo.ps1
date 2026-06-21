$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "Container status:"
docker compose --env-file .env.docker ps

Write-Host "`nHealth endpoint:"
Invoke-RestMethod -Uri "http://localhost:8000/health/" -TimeoutSec 5 | ConvertTo-Json

Write-Host "`nPostgreSQL version:"
docker compose --env-file .env.docker exec -T db `
    psql -U ibsec_user -d ibsec_lms -c "SELECT version();"

Write-Host "`nDjango database backend:"
docker compose --env-file .env.docker exec -T web `
    python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print(connection.vendor); print(connection.settings_dict['NAME'])"

Write-Host "`nDemo objects:"
docker compose --env-file .env.docker exec -T web `
    python manage.py shell -c "from django.contrib.auth.models import User; from courses.models import Course; from quizzes.models import Quiz; print('users=', User.objects.count()); print('demo_users=', list(User.objects.filter(username__in=['admin','security_officer','employee','employee2']).values_list('username', flat=True))); print('courses=', Course.objects.count()); print('quizzes=', Quiz.objects.count())"
