$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

docker compose `
    --env-file demo/.env `
    -f docker-compose.yml `
    -f demo/docker-compose.demo.yml `
    down -v --remove-orphans
