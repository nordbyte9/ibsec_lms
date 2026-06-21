# Docker-развертывание IBSec LMS на PostgreSQL 18

## Архитектура

Docker Compose запускает три сервиса:

1. `db` — PostgreSQL 18.4 Alpine;
2. `web` — Django под Gunicorn;
3. `nginx` — обратный прокси и сервер статических и загруженных файлов.

Данные сохраняются в именованных volumes:

- `postgres18_data` — каталог `/var/lib/postgresql`, соответствующий структуре официального образа PostgreSQL 18;
- `static_data`;
- `media_data`.

Сеть `backend` объявлена внутренней. Для локальной диагностики PostgreSQL дополнительно привязан только к `127.0.0.1:55432`; это не конфликтует с установленным на Windows PostgreSQL, который обычно занимает порт 5432. Внешний веб-доступ осуществляется через Nginx на `http://localhost:8000`.

## Готовый демонстрационный запуск

Архив содержит `.env.docker` с локальными демонстрационными параметрами. В Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\docker\start-demo.ps1
```

В Linux/macOS:

```bash
./docker/start-demo.sh
```

Ручной запуск:

```powershell
docker compose --env-file .env.docker config
docker compose --env-file .env.docker up --build -d
docker compose --env-file .env.docker ps
```

Приложение: `http://localhost:8000/`

Healthcheck: `http://localhost:8000/health/`

## Инициализация

При запуске контейнер `web` выполняет:

```bash
python manage.py check
python manage.py migrate --noinput
python manage.py seed_demo_once  # только при LOAD_DEMO_DATA=True
python manage.py collectstatic --noinput
```

Команда `seed_demo_once` проверяет наличие основных демонстрационных пользователей, курса и теста. Если они уже существуют, повторный вызов `seed_demo` пропускается, поэтому перезапуск контейнеров не создаёт повторные журнальные записи.

## Демо-данные

При `LOAD_DEMO_DATA=True` создаются:

- подразделения и должности;
- пользователи четырёх демонстрационных аккаунтов;
- учебные программы и категории ИБ;
- опубликованный курс «Основы информационной безопасности»;
- три урока;
- тест с вопросами и вариантами ответов;
- назначения, попытки тестирования и результаты;
- демонстрационные записи аудита и интеграций.

Аккаунты:

```text
admin / admin12345
security_officer / security_officer12345
employee / employee12345
employee2 / employee22345
```

## Проверка

Windows:

```powershell
.\docker\verify-demo.ps1
```

Ручные команды:

```powershell
docker compose --env-file .env.docker exec web python manage.py check
docker compose --env-file .env.docker exec web python manage.py test
docker compose --env-file .env.docker exec web python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print(connection.vendor); print(connection.settings_dict['NAME'])"
docker compose --env-file .env.docker exec db psql -U ibsec_user -d ibsec_lms -c "SELECT version();"
```

Ожидаемые значения:

```text
postgresql
ibsec_lms
PostgreSQL 18.4
```

## Подключение локальным psql

```powershell
psql -h localhost -p 55432 -U ibsec_user -d ibsec_lms
```

Пароль из готового demo-файла: `strong-password`.

Внутри `psql`:

```sql
SELECT current_database(), current_user, version();
\dt
```

## Логи и управление

```powershell
# Все логи
docker compose --env-file .env.docker logs -f

# Только Django
docker compose --env-file .env.docker logs -f web

# Остановка с сохранением данных
docker compose --env-file .env.docker down

# Полный сброс демо-окружения
docker compose --env-file .env.docker down -v --remove-orphans
```

Команда `down -v` удаляет только Docker volumes этого Compose-проекта. Локальная PostgreSQL-база вне Docker не затрагивается.

## Резервное копирование

```powershell
docker compose --env-file .env.docker exec -T db `
  pg_dump -U ibsec_user -d ibsec_lms > ibsec_lms_backup.sql
```

Восстановление:

```powershell
Get-Content .\ibsec_lms_backup.sql -Raw | `
  docker compose --env-file .env.docker exec -T db `
  psql -U ibsec_user -d ibsec_lms
```

## Важное отличие PostgreSQL 18

Начиная с PostgreSQL 18 официальный Docker-образ использует версионный `PGDATA` (`/var/lib/postgresql/18/docker`), а volume должен монтироваться в `/var/lib/postgresql`. Поэтому архив использует отдельный volume `postgres18_data` и не пытается запустить PostgreSQL 18 на старом volume от PostgreSQL 16.

## Ограничение текущего этапа

Nginx напрямую раздаёт `/media/` для совместимости с текущими ссылками `FileField`. Объектная авторизация файлов должна быть добавлена отдельным этапом усиления файлового хранилища.
