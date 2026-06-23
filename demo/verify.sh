#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

compose() {
    docker compose \
        --env-file demo/.env \
        -f docker-compose.yml \
        -f demo/docker-compose.demo.yml \
        "$@"
}

compose ps
curl --fail http://localhost:8000/health/
echo
compose exec -T web python manage.py check
compose exec -T web python manage.py test
