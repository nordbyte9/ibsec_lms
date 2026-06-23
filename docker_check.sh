#!/usr/bin/env bash
set -Eeuo pipefail

COMPOSE=(docker compose --env-file .env.docker)

show_diagnostics() {
    echo
    echo "Диагностика контейнеров:"
    "${COMPOSE[@]}" ps || true
    echo
    echo "Последние журналы контейнеров:"
    "${COMPOSE[@]}" logs --tail 120 || true
}

on_error() {
    local exit_code=$?
    echo
    echo "ОШИБКА: Docker-проверка завершилась с кодом ${exit_code}."
    show_diagnostics
    exit "${exit_code}"
}
trap on_error ERR

if ! command -v docker >/dev/null 2>&1; then
    echo "Docker не найден. Установите и запустите Docker Desktop/Docker Engine."
    exit 1
fi

if [[ ! -f .env.docker ]]; then
    echo "Не найден .env.docker."
    echo "Скопируйте .env.docker.example в .env.docker и замените SECRET_KEY, POSTGRES_PASSWORD и ALLOWED_HOSTS."
    exit 1
fi

if [[ ! -f docker-compose.yml ]]; then
    echo "Не найден docker-compose.yml. Запускайте скрипт из корня проекта IBSec LMS."
    exit 1
fi

echo "1/8 Проверка Docker и конфигурации Compose"
docker version
"${COMPOSE[@]}" version
"${COMPOSE[@]}" config --quiet

echo
echo "2/8 Остановка ранее запущенных контейнеров без удаления томов"
"${COMPOSE[@]}" down --remove-orphans

echo
echo "3/8 Сборка образа приложения"
"${COMPOSE[@]}" build --pull

echo
echo "4/8 Запуск PostgreSQL, Django/Gunicorn и Nginx"
"${COMPOSE[@]}" up -d

echo
echo "5/8 Ожидание HTTP health-check"
health_url="http://127.0.0.1:8000/health/"
healthy=0

for attempt in $(seq 1 40); do
    if command -v curl >/dev/null 2>&1; then
        if curl --fail --silent --show-error --max-time 3 "${health_url}" >/dev/null; then
            healthy=1
            break
        fi
    elif command -v wget >/dev/null 2>&1; then
        if wget --quiet --timeout=3 --tries=1 --spider "${health_url}"; then
            healthy=1
            break
        fi
    else
        if "${COMPOSE[@]}" exec -T nginx wget --quiet --timeout=3 --tries=1 --spider http://127.0.0.1/health/; then
            healthy=1
            echo "Предупреждение: curl/wget не найдены на хосте; endpoint проверен из контейнера nginx."
            break
        fi
    fi

    echo "Попытка ${attempt}/40: приложение ещё запускается..."
    sleep 3
done

if [[ "${healthy}" -ne 1 ]]; then
    echo "Приложение не ответило по адресу ${health_url}."
    false
fi

echo "Health-check успешен."

echo
echo "6/8 Проверка Django и миграций внутри контейнера"
"${COMPOSE[@]}" exec -T web python manage.py check
"${COMPOSE[@]}" exec -T web python manage.py migrate --check
"${COMPOSE[@]}" exec -T web python manage.py makemigrations --check --dry-run

echo
echo "7/8 Проверка централизованной ролевой модели"
"${COMPOSE[@]}" exec -T web python manage.py test tests.test_permissions --verbosity 2

echo
echo "8/8 Состояние контейнеров"
"${COMPOSE[@]}" ps

echo
echo "ПРОВЕРКА УСПЕШНО ЗАВЕРШЕНА."
echo "Проект доступен по адресу: http://127.0.0.1:8000/"
echo "Контейнеры оставлены запущенными. Для остановки:"
echo "docker compose --env-file .env.docker down"
