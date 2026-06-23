#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

docker compose \
    --env-file demo/.env \
    -f docker-compose.yml \
    -f demo/docker-compose.demo.yml \
    down -v --remove-orphans
