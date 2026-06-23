#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

if [ ! -f demo/.env ]; then
    cp demo/.env.example demo/.env
    echo "Created demo/.env. Replace all placeholder secrets, then run this script again."
    exit 1
fi

if grep -q 'replace-' demo/.env; then
    echo "demo/.env still contains placeholder secrets. Replace them before starting."
    exit 1
fi

docker compose \
    --env-file demo/.env \
    -f docker-compose.yml \
    -f demo/docker-compose.demo.yml \
    up --build -d

echo "IBSec LMS demo is available at http://localhost:8000/"
