# IBSec LMS

**IBSec LMS** — корпоративная информационная система обязательного обучения сотрудников требованиям информационной безопасности.

Система автоматизирует публикацию учебных материалов, назначение обязательных курсов, тестирование, контроль сроков, фиксацию результатов и формирование отчетности.

## Назначение проекта

Проект разрабатывается как:

1. учебный проект для преддипломной практики МУИВ;
2. основа выпускной квалификационной работы;
3. прототип корпоративной LMS для обучения по информационной безопасности.

## Фактический технологический стек

### Backend

- Python 3;
- Django 4.2.13;
- Django ORM;
- встроенная система аутентификации Django;
- Django Migrations;
- PostgreSQL — основная СУБД, поддерживаемая через `DATABASE_URL` или переменные `DB_*`;
- SQLite — автоматический fallback для локальной разработки;
- `psycopg2-binary` — драйвер PostgreSQL;
- `python-dotenv` — загрузка локального файла `.env`.

### Frontend

- Django Templates;
- HTML5;
- CSS;
- Bootstrap 5;
- JavaScript.

### Инфраструктура

- Git и GitHub;
- `.env` и переменные окружения для конфигурации приложения и базы данных;
- Docker и Docker Compose;
- Gunicorn;
- Nginx;
- PostgreSQL 18.4 в отдельном контейнере;
- GitHub Actions — запланирован.

> В проекте не используются Flask, Flask-Login, SQLAlchemy и Alembic. Управление моделями и схемой базы данных выполняется средствами Django ORM и Django Migrations.

## Архитектура

Проект реализован как модульный монолит на Django. Основные приложения:

- `accounts` — пользователи, роли, подразделения, должности и профиль;
- `courses` — учебные программы, курсы, уроки и материалы;
- `assignments` — назначение курсов сотрудникам и контроль сроков;
- `quizzes` — вопросы, варианты ответов, попытки и результаты тестирования;
- `reports` — аналитика и экспорт отчетных данных;
- `audit` — журнал действий;
- `integrations` — импорт организационной структуры и заготовки интеграций;
- `notifications` — модель уведомлений;
- `core` — общие страницы и служебная логика.

## Роли пользователей

В фактической модели реализованы три роли:

1. **Сотрудник (`employee`)**
   - просматривает назначенные курсы;
   - изучает материалы;
   - проходит тесты;
   - просматривает личный прогресс и результаты.

2. **Ответственный за ИБ (`security_officer`)**
   - управляет курсами в рамках прикладного интерфейса;
   - назначает обучение;
   - просматривает отчеты и журнал аудита;
   - контролирует прохождение обязательного обучения.

3. **Администратор (`admin`)**
   - имеет расширенные прикладные права;
   - управляет моделями и пользователями через Django Admin;
   - выполняет системное администрирование.

## Миграции базы данных

Проект использует штатный механизм Django Migrations:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations
```

Alembic для данного проекта не требуется, поскольку модели реализованы через Django ORM.

## Конфигурация баз данных

IBSec LMS выбирает подключение в следующем порядке:

1. `DATABASE_URL`;
2. `DB_ENGINE=postgresql` и переменные `DB_*`;
3. SQLite fallback.

Пример через URL:

```env
DATABASE_URL=postgresql://ibsec_user:password@localhost:5432/ibsec_lms
```

Пример через отдельные переменные:

```env
DB_ENGINE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ibsec_lms
DB_USER=ibsec_user
DB_PASSWORD=password
```

Без PostgreSQL-настроек используется `db.sqlite3`. Подробности приведены в `docs/database_configuration.md`.

## Основные функции

- регистрация и аутентификация;
- личный кабинет;
- ролевая модель доступа;
- управление курсами и уроками;
- загрузка учебных материалов;
- назначение обязательного обучения;
- тестирование и расчет результата;
- контроль прогресса;
- отчеты;
- CSV-экспорт;
- журнал аудита;
- Django Admin;
- раздел справки.

## Запуск через Docker Compose

Docker-окружение включает PostgreSQL 18.4, Django/Gunicorn и Nginx. Архив уже содержит локальный файл `.env.docker` с демонстрационными параметрами, поэтому для первого запуска достаточно:

```powershell
.\docker\start-demo.ps1
```

Либо вручную:

```powershell
docker compose --env-file .env.docker up --build -d
docker compose --env-file .env.docker ps
```

Для Linux/macOS:

```bash
./docker/start-demo.sh
```

Приложение будет доступно по адресу `http://localhost:8000/`. PostgreSQL контейнера доступен только с локального компьютера по адресу `localhost:55432`, поэтому он не конфликтует с установленным PostgreSQL на порту 5432. При первом запуске автоматически применяются Django-миграции, выполняется `collectstatic` и загружаются демонстрационные данные.

В готовом `.env.docker` установлено `LOAD_DEMO_DATA=True`. При первом запуске команда `seed_demo_once` создаёт пользователей, курс, уроки, тест, назначения, результаты и записи аудита. При повторном запуске данные не дублируются.

Демонстрационные аккаунты:

| Роль | Логин | Пароль |
|---|---|---|
| Администратор | `admin` | `admin12345` |
| Ответственный за ИБ | `security_officer` | `security_officer12345` |
| Сотрудник | `employee` | `employee12345` |
| Сотрудник 2 | `employee2` | `employee22345` |

Проверка окружения:

```powershell
.\docker\verify-demo.ps1
```

Подробная инструкция: `docs/docker_deployment.md`.

## Локальный запуск

```bash
git clone https://github.com/nordbyte9/ibsec_lms.git
cd ibsec_lms
git checkout practice/ib-compliance-training

python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Установка зависимостей и запуск с SQLite fallback:

```bash
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Приложение будет доступно по адресу `http://127.0.0.1:8000/`.

## Проверка проекта

```bash
python manage.py check
python manage.py test
python manage.py showmigrations
```

## Статус соответствия требованиям ПДП

Уже реализованы:

- клиент-серверное веб-приложение;
- PostgreSQL как основная СУБД и SQLite fallback;
- Docker Compose с PostgreSQL 18.4, Gunicorn и Nginx;
- healthchecks и persistent volumes;
- три роли;
- личный кабинет;
- административная панель;
- раздел справки;
- работа с файлами;
- более десяти экранных страниц;
- хранение исходного кода в GitHub.

Требуют завершения:

- экспорт XLSX и формирование DOCX;
- формальный подсчет логических строк;
- GitHub Actions;
- усиление тестирования и защиты файлов.
