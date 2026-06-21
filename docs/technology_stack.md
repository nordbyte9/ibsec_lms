# Фактический технологический стек IBSec LMS

## Серверная часть

- Python 3;
- Django 4.2.13;
- Django ORM;
- Django Authentication;
- Django Admin;
- Django Migrations;
- WSGI/ASGI-интерфейсы Django.

## Клиентская часть

- Django Templates;
- HTML5;
- CSS;
- Bootstrap 5;
- JavaScript.

## Данные

- PostgreSQL 18.4 — основная СУБД;
- SQLite — fallback для локальной разработки;
- `psycopg2-binary` — драйвер PostgreSQL;
- `python-dotenv` — загрузка `.env`;
- конфигурация через `DATABASE_URL` или `DB_*`.

## Файлы

- `FileField`;
- `MEDIA_ROOT`;
- `MEDIA_URL`;
- локальное файловое хранилище Django.

## Инфраструктура

- Git;
- GitHub;
- переменные окружения;
- Docker и Docker Compose;
- Gunicorn;
- Nginx;
- healthchecks и persistent volumes;
- GitHub Actions — следующий этап.

## Миграции

Изменения структуры БД создаются и применяются командами:

```bash
python manage.py makemigrations
python manage.py migrate
```

Alembic не используется и не требуется.

## Формулировка для отчета ПДП

> Программная система IBSec LMS реализована на языке Python с использованием веб-фреймворка Django 4.2.13. Доступ к данным выполняется посредством Django ORM, а управление изменениями схемы базы данных — встроенным механизмом Django Migrations. Пользовательский интерфейс сформирован серверными шаблонами Django с применением HTML, CSS, JavaScript и Bootstrap 5. В качестве основной SQL-СУБД поддерживается PostgreSQL, подключаемая через `DATABASE_URL` или переменные `DB_*`; для локальной разработки предусмотрен автоматический fallback на SQLite. Контейнерное развертывание реализовано средствами Docker Compose и включает сервисы PostgreSQL 18.4, Django/Gunicorn и Nginx, а сохранность данных обеспечивается именованными volumes.
