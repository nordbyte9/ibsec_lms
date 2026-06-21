# База данных

Проект IBSec LMS поддерживает два режима работы:

- `SQLite` — локальный запуск без дополнительной настройки.
- `PostgreSQL` — основной вариант для развёртывания и демонстрации готовности к промышленной SQL-БД.

## Локальный запуск на SQLite

Если переменная `DB_ENGINE` не задана, проект использует SQLite-файл `db.sqlite3` в корне репозитория.

Команды:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Настройка PostgreSQL

Чтобы включить PostgreSQL, задайте переменные окружения:

- `DB_ENGINE=postgresql`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

Пример:

```env
DB_ENGINE=postgresql
DB_NAME=ibsec_lms
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

После настройки выполните:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Примечания

- При отсутствии `DB_ENGINE` проект остаётся на SQLite.
- `migrate` применяет схему базы данных.
- `createsuperuser` создаёт административный аккаунт для входа в Django admin.
