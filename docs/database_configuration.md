# Настройка базы данных IBSec LMS

IBSec LMS использует PostgreSQL в серверном окружении и поддерживает SQLite для локальной разработки.

## Приоритет настроек

Подключение выбирается в следующем порядке:

1. `DATABASE_URL`;
2. `DB_ENGINE=postgresql` и переменные `DB_*`;
3. SQLite.

Неизвестное значение `DB_ENGINE` и неполный набор PostgreSQL-параметров приводят к ошибке запуска. Это предотвращает незаметное переключение серверного окружения на SQLite.

## Локальный файл `.env`

Создание файла конфигурации:

```bash
cp .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

Файл `.env` исключён из Git. Переменные операционной системы имеют приоритет над значениями из файла.

## SQLite

```env
DB_ENGINE=sqlite
SQLITE_PATH=db.sqlite3
```

Применение миграций:

```bash
python manage.py migrate
python manage.py runserver
```

SQLite предназначен для локальной разработки и автоматических тестов. Для многопользовательского серверного запуска следует использовать PostgreSQL.

## PostgreSQL через `DATABASE_URL`

```env
DATABASE_URL=postgresql://ibsec_user:replace-with-a-strong-password@localhost:5432/ibsec_lms
```

Параметры соединения можно передавать в query string:

```env
DATABASE_URL=postgresql://ibsec_user:replace-with-a-strong-password@db.example.com:5432/ibsec_lms?sslmode=require
```

Специальные символы в логине и пароле должны быть URL-кодированы.

## PostgreSQL через `DB_*`

```env
DATABASE_URL=
DB_ENGINE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ibsec_lms
DB_USER=ibsec_user
DB_PASSWORD=replace-with-a-strong-password
DB_CONN_MAX_AGE=60
DB_CONN_HEALTH_CHECKS=True
```

Для защищённого внешнего подключения можно задать:

```env
DB_SSLMODE=require
```

## Проверка подключения

```bash
python manage.py check
python manage.py migrate --check
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print(connection.vendor); print(connection.settings_dict['NAME'])"
```

Для PostgreSQL значение `connection.vendor` должно быть `postgresql`.

## Миграции

```bash
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py showmigrations
```

Перед развёртыванием новой версии необходимо создать резервную копию базы данных и проверить миграции на тестовом окружении.
