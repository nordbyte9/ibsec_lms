$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker CLI not found. Install or start Docker Desktop."
}

if (-not (Test-Path ".env.docker")) {
    Copy-Item ".env.docker.example" ".env.docker"
    Write-Warning "Created .env.docker from the example. Set SECRET_KEY and POSTGRES_PASSWORD before production use."
}

Write-Host "Validating Docker Compose configuration..."
docker compose --env-file .env.docker config | Out-Null

Write-Host "Building and starting IBSec LMS with PostgreSQL 18..."
docker compose --env-file .env.docker up --build -d

Write-Host "Waiting for the application health endpoint..."
$ready = $false
for ($attempt = 1; $attempt -le 90; $attempt++) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health/" -TimeoutSec 3
        if ($response.status -eq "ok") {
            $ready = $true
            break
        }
    }
    catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $ready) {
    docker compose --env-file .env.docker ps
    docker compose --env-file .env.docker logs --tail 150 db web nginx
    throw "IBSec LMS did not become healthy within the expected time."
}

Write-Host ""
Write-Host "IBSec LMS is ready: http://localhost:8000/" -ForegroundColor Green
Write-Host "Admin panel: http://localhost:8000/admin/"
Write-Host "PostgreSQL host endpoint: localhost:55432"
Write-Host ""
Write-Host "Demo accounts:"
Write-Host "  admin / admin12345"
Write-Host "  security_officer / security_officer12345"
Write-Host "  employee / employee12345"
Write-Host "  employee2 / employee22345"
Write-Host ""

docker compose --env-file .env.docker ps
