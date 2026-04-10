# Deployment

Этот документ описывает базовые шаги для локального запуска проекта и подготовки к продакшну.

## 1. Как создать виртуальное окружение

```bash
python -m venv .venv
source .venv/bin/activate
```

Для Windows:

```bash
.venv\Scripts\activate
```

## 2. Как установить зависимости

```bash
pip install -r requirements.txt
```

Если используется `pip-tools`, `poetry` или другой менеджер зависимостей, добавьте сюда нужную команду.

## 3. Как применить миграции

```bash
python manage.py migrate
```

## 4. Заполнение демо-данными

```bash
python manage.py seed_demo
```

## 5. Как создать суперпользователя

```bash
python manage.py createsuperuser
```

## 6. Как запустить сервер

```bash
python manage.py runserver
```

По умолчанию сервер будет доступен по адресу:

```text
http://127.0.0.1:8000/
```

## 7. Сборка статических файлов

```bash
python manage.py collectstatic
```

## 8. Что нужно для продакшна

Перед деплоем необходимо проверить следующее:

- настроены переменные окружения;
- задан SECRET_KEY;
- установлен DEBUG=False;
- заполнен ALLOWED_HOSTS;
- настроена база данных;
- для production рекомендуется использовать PostgreSQL;
- выполнена сборка статических файлов;
- настроен веб-сервер, например Nginx;
- настроен WSGI/ASGI-сервер, например Gunicorn или Uvicorn;
- включены HTTPS, логирование и резервное копирование.

## 9. Переменные окружения

Для продакшна рекомендуется вынести настройки в переменные окружения, например:

- SECRET_KEY
- DEBUG
- ALLOWED_HOSTS
- DB_NAME
- DB_USER
- DB_PASSWORD
- DB_HOST
- DB_PORT
