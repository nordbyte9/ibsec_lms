#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

if [ ! -f .env.docker ]; then
    cp .env.docker.example .env.docker
    echo "Created .env.docker from the example. Change secrets before production use."
fi

docker compose --env-file .env.docker config >/dev/null
docker compose --env-file .env.docker up --build -d

attempt=1
while [ "$attempt" -le 90 ]; do
    if curl --fail --silent http://localhost:8000/health/ >/dev/null 2>&1; then
        echo "IBSec LMS is ready: http://localhost:8000/"
        echo "Demo: admin/admin12345, security_officer/security_officer12345, employee/employee12345"
        docker compose --env-file .env.docker ps
        exit 0
    fi
    sleep 2
    attempt=$((attempt + 1))
done

docker compose --env-file .env.docker logs --tail 150 db web nginx
exit 1
