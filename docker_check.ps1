$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-DockerCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    Write-Host "`n> docker $($Arguments -join ' ')" -ForegroundColor Cyan
    & docker @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Команда docker завершилась с кодом $LASTEXITCODE."
    }
}

function Show-DockerDiagnostics {
    Write-Host "`nДиагностика контейнеров:" -ForegroundColor Yellow
    & docker compose --env-file .env.docker ps

    Write-Host "`nПоследние журналы контейнеров:" -ForegroundColor Yellow
    & docker compose --env-file .env.docker logs --tail 120
}

try {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker не найден. Запустите Docker Desktop и повторите проверку."
    }

    Invoke-DockerCommand -Arguments @("version")
    Invoke-DockerCommand -Arguments @("compose", "version")

    if (-not (Test-Path ".env.docker" -PathType Leaf)) {
        throw "Не найден .env.docker. Скопируйте .env.docker.example в .env.docker и замените значения SECRET_KEY, POSTGRES_PASSWORD и ALLOWED_HOSTS."
    }

    if (-not (Test-Path "docker-compose.yml" -PathType Leaf)) {
        throw "Не найден docker-compose.yml. Запускайте скрипт из корня проекта IBSec LMS."
    }

    Write-Host "`n1/8 Проверка конфигурации Docker Compose" -ForegroundColor Green
    Invoke-DockerCommand -Arguments @("compose", "--env-file", ".env.docker", "config", "--quiet")

    Write-Host "`n2/8 Остановка ранее запущенных контейнеров без удаления томов" -ForegroundColor Green
    Invoke-DockerCommand -Arguments @("compose", "--env-file", ".env.docker", "down", "--remove-orphans")

    Write-Host "`n3/8 Сборка образа приложения" -ForegroundColor Green
    Invoke-DockerCommand -Arguments @("compose", "--env-file", ".env.docker", "build", "--pull")

    Write-Host "`n4/8 Запуск PostgreSQL, Django/Gunicorn и Nginx" -ForegroundColor Green
    Invoke-DockerCommand -Arguments @("compose", "--env-file", ".env.docker", "up", "-d")

    Write-Host "`n5/8 Ожидание HTTP health-check" -ForegroundColor Green
    $healthUrl = "http://127.0.0.1:8000/health/"
    $healthy = $false

    for ($attempt = 1; $attempt -le 40; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
                $healthy = $true
                Write-Host "Health-check успешен: HTTP $($response.StatusCode)" -ForegroundColor Green
                break
            }
        }
        catch {
            Write-Host "Попытка $attempt/40: приложение ещё запускается..."
        }

        Start-Sleep -Seconds 3
    }

    if (-not $healthy) {
        throw "Приложение не ответило по адресу $healthUrl."
    }

    Write-Host "`n6/8 Проверка Django и миграций внутри контейнера" -ForegroundColor Green
    Invoke-DockerCommand -Arguments @("compose", "--env-file", ".env.docker", "exec", "-T", "web", "python", "manage.py", "check")
    Invoke-DockerCommand -Arguments @("compose", "--env-file", ".env.docker", "exec", "-T", "web", "python", "manage.py", "migrate", "--check")
    Invoke-DockerCommand -Arguments @("compose", "--env-file", ".env.docker", "exec", "-T", "web", "python", "manage.py", "makemigrations", "--check", "--dry-run")

    Write-Host "`n7/8 Проверка централизованной ролевой модели" -ForegroundColor Green
    Invoke-DockerCommand -Arguments @("compose", "--env-file", ".env.docker", "exec", "-T", "web", "python", "manage.py", "test", "tests.test_permissions", "--verbosity", "2")

    Write-Host "`n8/8 Состояние контейнеров" -ForegroundColor Green
    Invoke-DockerCommand -Arguments @("compose", "--env-file", ".env.docker", "ps")

    Write-Host "`nПРОВЕРКА УСПЕШНО ЗАВЕРШЕНА." -ForegroundColor Green
    Write-Host "Проект доступен по адресу: http://127.0.0.1:8000/"
    Write-Host "Контейнеры оставлены запущенными. Для остановки:"
    Write-Host "docker compose --env-file .env.docker down"
}
catch {
    Write-Host "`nОШИБКА: $($_.Exception.Message)" -ForegroundColor Red
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Show-DockerDiagnostics
    }
    exit 1
}
