# Настройка базы данных IBSec LMS

IBSec LMS поддерживает PostgreSQL как основную СУБД и SQLite как fallback для локальной разработки.

## Приоритет конфигурации

Настройки выбираются в следующем порядке:

1. если задан `DATABASE_URL`, используется он;
2. иначе, если `DB_ENGINE=postgresql`, подключение собирается из `DB_*`;
3. иначе используется SQLite.

Если `DB_ENGINE` содержит неизвестное значение или PostgreSQL-настройки заполнены не полностью, приложение завершает запуск с понятной ошибкой. Это защищает production-среду от незаметного запуска на SQLite.

## Загрузка `.env`

Файл `.env` автоматически загружается из корня проекта через `python-dotenv`. Уже заданные переменные операционной системы имеют приоритет над `.env`.

Создание локального файла:

```bash
cp .env.example .env
```

В Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Файл `.env` не должен попадать в Git.

## Вариант 1: SQLite fallback

Для локальной разработки достаточно:

```env
DB_ENGINE=sqlite
SQLITE_PATH=db.sqlite3
```

Если переменные базы данных отсутствуют полностью, будет выбран тот же SQLite-файл `db.sqlite3` в корне проекта.

Применение миграций:

```bash
python manage.py migrate
python manage.py runserver
```

## Вариант 2: PostgreSQL через `DATABASE_URL`

`DATABASE_URL` имеет наивысший приоритет:

```env
DATABASE_URL=postgresql://ibsec_user:strong-password@localhost:5432/ibsec_lms
```

Дополнительные параметры PostgreSQL можно передавать в query string:

```env
DATABASE_URL=postgresql://ibsec_user:strong-password@localhost:5432/ibsec_lms?sslmode=require
```

Если пароль содержит специальные символы, их нужно URL-кодировать.

## Вариант 3: PostgreSQL через `DB_*`

```env
DATABASE_URL=
DB_ENGINE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ibsec_lms
DB_USER=ibsec_user
DB_PASSWORD=strong-password
DB_CONN_MAX_AGE=60
DB_CONN_HEALTH_CHECKS=True
```

Для сервера с обязательным TLS:

```env
DB_SSLMODE=require
```

## Создание пользователя и базы PostgreSQL

Пример команд из `psql` под административной учетной записью:

```sql
CREATE USER ibsec_user WITH PASSWORD 'strong-password';
CREATE DATABASE ibsec_lms OWNER ibsec_user;
GRANT ALL PRIVILEGES ON DATABASE ibsec_lms TO ibsec_user;
```

После настройки `.env`:

```bash
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Проверка активной СУБД

```bash
python manage.py shell -c "from django.db import connection; print(connection.vendor); print(connection.settings_dict['NAME'])"
```

Ожидаемые значения `connection.vendor`:

- `sqlite` — локальный fallback;
- `postgresql` — основная СУБД.

## Перенос демонстрационных данных SQLite → PostgreSQL

Миграции создают структуру таблиц, но не переносят существующие записи автоматически.

Перед переключением с SQLite:

```bash
python manage.py dumpdata --natural-foreign --natural-primary \
  --exclude contenttypes --exclude auth.permission \
  --indent 2 > data.json
```

После переключения на PostgreSQL:

```bash
python manage.py migrate
python manage.py loaddata data.json
```

Перенос необходимо сначала проверить на резервной базе.

## Проверки перед коммитом

```bash
python -m unittest tests.test_database_config
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test
```

## Почему используется Django Migrations

Проект работает на Django ORM, поэтому схема SQLite и PostgreSQL управляется одним набором Django-миграций. Alembic не требуется.

## Docker: PostgreSQL 18

Docker Compose использует официальный образ `postgres:18.4-alpine`. Внутри сети Compose Django подключается к `db:5432`. Для локальной диагностики база доступна на `127.0.0.1:55432`, чтобы не конфликтовать с локальным PostgreSQL на порту 5432.

```powershell
psql -h localhost -p 55432 -U ibsec_user -d ibsec_lms
```

Путь данных PostgreSQL 18: `/var/lib/postgresql/18/docker`; именованный volume монтируется в `/var/lib/postgresql`.
