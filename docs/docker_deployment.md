# Docker-развёртывание IBSec LMS

## Состав окружения

`docker-compose.yml` запускает три сервиса:

1. `db` — PostgreSQL 18.4 Alpine;
2. `web` — Django под Gunicorn;
3. `nginx` — обратный прокси и раздача статических файлов.

Данные сохраняются в именованных volumes:

- `postgres18_data` — база данных;
- `static_data` — собранные статические файлы;
- `media_data` — загруженные материалы.

Сеть базы данных объявлена внутренней. Порт PostgreSQL публикуется только на `127.0.0.1` для локальной диагностики.

## Подготовка конфигурации

Windows:

```powershell
Copy-Item .env.docker.example .env.docker
```

Linux/macOS:

```bash
cp .env.docker.example .env.docker
```

Перед запуском замените все значения с префиксом `replace-`. Для публичного домена также задайте корректные `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS`.

Файл `.env.docker` содержит секреты и не должен попадать в Git.

## Запуск

```bash
docker compose --env-file .env.docker config
docker compose --env-file .env.docker up --build -d
```

При старте контейнер `web` выполняет:

```text
python manage.py check
python manage.py migrate --noinput
python manage.py migrate --check
python manage.py collectstatic --noinput
```

Создание первого администратора:

```bash
docker compose --env-file .env.docker exec web python manage.py createsuperuser
```

Проверка состояния:

```bash
docker compose --env-file .env.docker ps
curl --fail http://localhost:8000/health/
docker compose --env-file .env.docker exec web python manage.py check
```

## Логи и управление

```bash
# Все сервисы
docker compose --env-file .env.docker logs -f

# Только приложение
docker compose --env-file .env.docker logs -f web

# Остановка с сохранением данных
docker compose --env-file .env.docker down
```

Команда `down -v` удаляет базу данных и загруженные файлы этого Compose-проекта. В рабочем окружении её следует использовать только при осознанном полном сбросе.

## Резервное копирование PostgreSQL

```bash
docker compose --env-file .env.docker exec -T db \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" > ibsec_lms_backup.sql
```

Для PowerShell удобнее явно указать значения пользователя и базы из `.env.docker`:

```powershell
docker compose --env-file .env.docker exec -T db `
  pg_dump -U ibsec_user -d ibsec_lms > ibsec_lms_backup.sql
```

Перед восстановлением проверьте целевую базу и версию PostgreSQL.

## PostgreSQL 18

Официальный образ PostgreSQL 18 использует версионный каталог `PGDATA` внутри `/var/lib/postgresql`. Поэтому volume монтируется в `/var/lib/postgresql`, а контейнер самостоятельно создаёт нужную внутреннюю структуру.

## Демонстрационный контур

Демонстрационные пользователи и данные не подключены к обычному Compose-запуску. Для них используется отдельный override и настройки из каталога [`demo/`](../demo/README.md).

## Текущее ограничение файлового хранилища

Nginx напрямую раздаёт `/media/` для совместимости с текущими ссылками Django `FileField`. До внедрения объектной авторизации загруженные материалы следует размещать только в доверенном внутреннем контуре и не публиковать media endpoint в открытом интернете.
