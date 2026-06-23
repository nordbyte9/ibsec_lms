$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path "demo/.env")) {
    Copy-Item "demo/.env.example" "demo/.env"
    throw "Created demo/.env. Replace all placeholder secrets, then run the script again."
}

if (Select-String -Path "demo/.env" -Pattern "replace-" -Quiet) {
    throw "demo/.env still contains placeholder secrets. Replace them before starting."
}

docker compose `
    --env-file demo/.env `
    -f docker-compose.yml `
    -f demo/docker-compose.demo.yml `
    up --build -d

Write-Host "IBSec LMS demo is available at http://localhost:8000/" -ForegroundColor Green
