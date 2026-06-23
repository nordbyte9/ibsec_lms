$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$ComposeArgs = @(
    "compose",
    "--env-file", "demo/.env",
    "-f", "docker-compose.yml",
    "-f", "demo/docker-compose.demo.yml"
)

& docker @ComposeArgs ps
Invoke-RestMethod -Uri "http://localhost:8000/health/" -TimeoutSec 5 | ConvertTo-Json
& docker @ComposeArgs exec -T web python manage.py check
& docker @ComposeArgs exec -T web python manage.py test
