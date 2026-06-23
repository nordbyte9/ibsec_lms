# Развёртывание

## Локальная разработка

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

В Windows используйте `.venv\Scripts\Activate.ps1` и `Copy-Item .env.example .env`.

## Docker Compose

Основная инструкция: [../docker_deployment.md](../docker_deployment.md).

```bash
cp .env.docker.example .env.docker
docker compose --env-file .env.docker up --build -d
docker compose --env-file .env.docker exec web python manage.py createsuperuser
```

## Контроль перед публикацией

- `DEBUG=False`;
- `SECRET_KEY` хранится вне Git;
- `ALLOWED_HOSTS` содержит только рабочие домены;
- `CSRF_TRUSTED_ORIGINS` использует HTTPS-адреса;
- настроена PostgreSQL;
- применены миграции;
- выполнен `collectstatic`;
- настроены HTTPS, резервное копирование и централизованные логи;
- демонстрационный override не используется.
