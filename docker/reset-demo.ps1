$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Warning "This removes the Docker PostgreSQL 18 database and uploaded files."
docker compose --env-file .env.docker down -v --remove-orphans
& "$PSScriptRoot\start-demo.ps1"
