# IBSec LMS

**IBSec LMS** — корпоративная система обязательного обучения сотрудников требованиям информационной безопасности.

Система объединяет управление курсами, назначение обязательного обучения, тестирование знаний, контроль сроков, аудит действий и формирование отчётных документов.

## Возможности

- управление пользователями, подразделениями, должностями и ролями;
- публикация курсов, уроков и учебных материалов;
- назначение обязательного обучения сотрудникам;
- тестирование с ограничением времени и количества попыток;
- контроль прогресса, сроков и результатов;
- отчёты по сотрудникам, подразделениям и курсам;
- экспорт CSV и XLSX;
- формирование DOCX-сертификатов;
- журнал аудита действий;
- импорт организационной структуры из CSV;
- административный интерфейс Django Admin;
- запуск с PostgreSQL в Docker Compose;
- SQLite для локальной разработки.

## Архитектура

Приложение реализовано как модульный монолит на Django:

- `accounts` — пользователи, роли, подразделения, должности и профили;
- `courses` — программы обучения, курсы, уроки и материалы;
- `assignments` — назначения курсов и контроль сроков;
- `quizzes` — вопросы, варианты ответов, попытки и результаты;
- `reports` — аналитика и экспорт документов;
- `audit` — журнал действий;
- `integrations` — импорт организационной структуры из CSV;
- `notifications` — уведомления;
- `core` — общие страницы, навигация и health endpoint.

## Роли

### Сотрудник (`employee`)

Просматривает назначенные курсы, изучает материалы, проходит тесты и контролирует собственный прогресс.

### Ответственный за ИБ (`security_officer`)

Управляет курсами и назначениями, контролирует прохождение обучения, просматривает отчёты, аудит и результаты импорта.

### Администратор (`admin`)

Имеет расширенные прикладные права и доступ к Django Admin для системного администрирования.

## Технологии

- Python 3.12;
- Django 4.2;
- PostgreSQL 18;
- SQLite для локальной разработки;
- Gunicorn и Nginx;
- Docker Compose;
- Bootstrap 5;
- `openpyxl` для XLSX;
- `python-docx` для DOCX.

Подробный состав приведён в [docs/technology_stack.md](docs/technology_stack.md).

## Локальный запуск

### 1. Подготовка окружения

```bash
git clone https://github.com/nordbyte9/ibsec_lms.git
cd ibsec_lms
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
```

Linux/macOS:

```bash
source .venv/bin/activate
cp .env.example .env
```

### 2. Установка и инициализация

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

При стандартном содержимом `.env.example` используется локальная SQLite-база. Приложение доступно на `http://127.0.0.1:8000/`.

## Запуск через Docker Compose

Скопируйте шаблон конфигурации и замените все значения-заглушки:

Windows:

```powershell
Copy-Item .env.docker.example .env.docker
```

Linux/macOS:

```bash
cp .env.docker.example .env.docker
```

Запуск:

```bash
docker compose --env-file .env.docker config
docker compose --env-file .env.docker up --build -d
docker compose --env-file .env.docker exec web python manage.py createsuperuser
```

Приложение доступно на `http://localhost:8000/`, health endpoint — на `http://localhost:8000/health/`.

Подробности приведены в [docs/docker_deployment.md](docs/docker_deployment.md).

## База данных

Параметры выбираются в следующем порядке:

1. `DATABASE_URL`;
2. `DB_ENGINE=postgresql` и переменные `DB_*`;
3. SQLite.

Пример PostgreSQL через отдельные переменные:

```env
DB_ENGINE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ibsec_lms
DB_USER=ibsec_user
DB_PASSWORD=replace-with-a-strong-password
```

Подробности: [docs/database_configuration.md](docs/database_configuration.md).

## Импорт организационной структуры

CSV-файл должен содержать заголовки:

```text
username,email,first_name,last_name,department,position,role
```

Запуск импорта:

```bash
python manage.py import_org_csv docs/examples/org_structure_import.csv
```

Операция создаёт или обновляет пользователей, подразделения, должности и роли. Результат сохраняется в журнале импорта.

## Экспорт документов

- XLSX-реестр формируется из отчёта по сотрудникам;
- DOCX-сертификат доступен после успешного завершения назначенного курса;
- операции экспорта фиксируются в журнале аудита.

Реквизиты сертификатов задаются переменными:

```env
DOCUMENT_ORGANIZATION_NAME=IBSec LMS
DOCUMENT_SIGNER_TITLE=Ответственный за информационную безопасность
DOCUMENT_SIGNER_NAME=
```

Подробности: [docs/document_exports.md](docs/document_exports.md).

## Демонстрационное окружение

Тестовые пользователи и данные полностью отделены от обычного запуска. Инструкции и Docker-override находятся в [demo/README.md](demo/README.md). Демо-пароли задаются только в локальном файле `demo/.env`, который исключён из Git.

## Проверка

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

GitHub Actions выполняет эти проверки для push и pull request.

## Документация

- [Настройка базы данных](docs/database_configuration.md)
- [Docker-развёртывание](docs/docker_deployment.md)
- [Экспорт XLSX и DOCX](docs/document_exports.md)
- [Технологический стек](docs/technology_stack.md)
- [Изолированное демо-окружение](demo/README.md)
