# IBSec LMS

**IBSec LMS** — корпоративная система обязательного обучения сотрудников требованиям информационной безопасности (ИБ).

Проект ориентирован на внутренние регламенты компании: назначение обязательных ИБ-курсов, проверку знаний, фиксацию прохождения и формирование отчетности для контроля выполнения требований.

## Цель проекта

Цель проекта — автоматизировать цикл обязательного ИБ-обучения сотрудников:
- доведение обязательных материалов до сотрудников;
- проверка усвоения через тестирование;
- фиксация результатов и прогресса;
- предоставление отчетности для ответственных лиц.

## Чем отличается от типовой LMS

Типовая LMS обычно ориентирована на широкий образовательный процесс (много форматов обучения, гибкие учебные траектории, внешние курсы).

IBSec LMS в текущей реализации ориентирована на **комплаенс-задачу**:
- приоритет обязательного, а не факультативного обучения;
- контроль прохождения по ролям и подразделениям;
- акцент на проверяемой отчетности (аналитика и CSV-выгрузка);
- минимально необходимый набор сущностей для ИБ-инструктажей и тестов.

## Роли пользователей

В системе реализованы 3 роли:

1. **Сотрудник (`employee`)**
- проходит назначенные курсы и тесты;
- видит личный прогресс.

2. **Преподаватель/ИБ-ответственный (`instructor`)**
- создает курсы и уроки;
- просматривает аналитику;
- выгружает результаты в CSV.

3. **Администратор (`admin`)**
- имеет возможности преподавателя;
- управляет системой через Django admin (`/admin/`).

## Бизнес-процесс обязательного ИБ-обучения

1. ИБ-ответственный готовит и публикует курс.
2. В курс добавляются материалы (текст, ссылка, файл) и тест.
3. Сотрудник проходит обучение и тестирование.
4. Система сохраняет попытку, балл и факт прохождения порога.
5. Сотрудник отслеживает личный прогресс в личном кабинете.
6. ИБ-ответственный/администратор анализирует сводные результаты и при необходимости выгружает их в CSV.

## Основные функции системы

- аутентификация, регистрация, личный профиль;
- ролевая модель доступа (3 роли);
- каталог курсов и карточка курса;
- создание курсов и уроков;
- уроки трех типов: текст, ссылка, файл;
- тестирование с автопроверкой;
- расчет процента и проверка порога прохождения;
- личный кабинет сотрудника с прогрессом;
- аналитика для `instructor`/`admin`;
- экспорт результатов в CSV;
- административная панель Django.

## Технологический стек

- Python 3
- Django 4.2.13
- Django ORM
- SQLite (по умолчанию)
- PostgreSQL (поддерживается через настройку `DATABASES`)
- HTML + Django Templates
- Bootstrap 5 (CDN)
- psycopg2-binary

## Инструкция запуска

### 1. Клонирование и переход в проект

```bash
git clone <repository_url>
cd ibsec_lms
```

### 2. Виртуальное окружение

```bash
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

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Применение миграций

```bash
python manage.py migrate
```

### 5. (Опционально) Заполнение демо-данными

```bash
python manage.py seed_demo
```

### 6. (Опционально) Создание суперпользователя

```bash
python manage.py createsuperuser
```

### 7. Запуск сервера

```bash
python manage.py runserver
```

Приложение будет доступно по адресу:

`http://127.0.0.1:8000/`

## Ключевые разделы интерфейса

- `/` — главная страница;
- `/accounts/login/`, `/accounts/signup/`, `/accounts/profile/`;
- `/courses/`, `/courses/<id>/`, `/courses/create/`;
- `/quizzes/course/<course_id>/`, `/quizzes/take/<quiz_id>/`, `/quizzes/result/<submission_id>/`;
- `/reports/my/`, `/reports/analytics/`, `/reports/export/`;
- `/admin/`.

Этого достаточно для требования по наличию 10+ страниц в учебном проекте.

## Структура проекта

- `accounts` — пользователи, роли, профиль;
- `courses` — курсы и уроки;
- `quizzes` — тестирование и результаты;
- `reports` — личный прогресс, аналитика, экспорт;
- `notifications` — модель уведомлений и отправка email;
- `core` — главная страница и служебные команды.

## Privacy and Security Notice

The system stores the following categories of personal data:
- account identifiers and contact data (`username`, `email`, names);
- role and profile data;
- department and position references;
- course assignments and due dates;
- quiz attempts, scores, and completion timestamps;
- audit logs with IP address and user agent.

Access is role-based:
- `employee` sees only their own assignments, quiz history, and progress;
- `security_officer` sees reports, assignments, quiz results, and audit logs for control purposes;
- `admin` has the broadest operational access, including audit review and system administration.

Protection measures used in the project:
- Django authentication and permission checks in views;
- role-based access control for sensitive pages;
- password hashing handled by Django;
- audit logging for assignments, quiz submissions, completions, and CSV exports;
- limited exposure of personal data in reports and templates.

The audit journal is required to track operational actions, support accountability, and investigate access or processing events affecting training data.
