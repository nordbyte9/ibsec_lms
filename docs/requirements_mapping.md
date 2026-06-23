# Сопоставление требований ПДП и реализации IBSec LMS

| Требование | Фактическая реализация | Статус |
|---|---|---|
| Клиент-серверная архитектура | Django-приложение, браузерный клиент, HTTP-маршруты, серверные шаблоны | Выполнено |
| Язык и фреймворк | Python 3, Django 4.2.13 | Выполнено |
| ORM | Django ORM | Выполнено |
| Миграции | Django Migrations | Выполнено |
| SQL-СУБД | PostgreSQL как основная СУБД, SQLite как fallback | Выполнено |
| PostgreSQL | `DATABASE_URL` или `DB_ENGINE=postgresql` с `DB_*` | Выполнено |
| Не менее трех ролей | `employee`, `security_officer`, `admin` | Выполнено |
| Личный кабинет | профиль, назначения, прогресс и результаты | Выполнено |
| Административная панель | Django Admin | Выполнено |
| Раздел справки | отдельная страница `/help/` | Выполнено |
| Курсы и материалы | приложения `courses` и `lessons`, текстовые, ссылочные и файловые уроки | Выполнено |
| Тестирование | приложение `quizzes`, вопросы, варианты, попытки и результаты | Выполнено |
| Назначение обучения | приложение `assignments` | Выполнено |
| Отчетность | экранные отчёты, CSV, XLSX-реестр и DOCX-сертификаты | Выполнено |
| Формирование XLSX/DOCX | XLSX-реестр и DOCX-сертификаты | Выполнено |
| Работа с файловой системой | загрузка файлов через Django `FileField` | Частично |
| Журнал аудита | приложение `audit` | Выполнено |
| Не менее десяти экранных форм | в проекте присутствует более десяти страниц | Выполнено, требуется формальный реестр |
| Docker | Dockerfile, Docker Compose, PostgreSQL 18.4, Gunicorn, Nginx, healthchecks и volumes | Выполнено |
| CI/CD | GitHub Actions отсутствует | Не выполнено |
| Исходный код в Git | GitHub, отдельная рабочая ветка | Выполнено |

## Фактический стек

```text
Python 3
Django 4.2.13
Django ORM
Django Authentication
Django Migrations
Django Templates
PostgreSQL + SQLite fallback
PostgreSQL driver: psycopg2-binary
Environment loader: python-dotenv
Docker Compose
Gunicorn
Nginx
openpyxl
python-docx
Bootstrap 5
HTML/CSS/JavaScript
```

## Неиспользуемые технологии

Следующие технологии не относятся к текущей реализации и не должны указываться в отчете:

```text
Flask
Flask-Login
SQLAlchemy
Alembic
Jinja2 как отдельный шаблонизатор
```

Django Templates синтаксически родственны Jinja-подобным шаблонам, но в проекте используется именно встроенный шаблонный движок Django.
