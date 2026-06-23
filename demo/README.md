# Изолированное демонстрационное окружение

Каталог `demo/` не участвует в обычном запуске IBSec LMS. Демонстрационные management-команды подключаются только через `ibsec_lms.settings_demo`, а Docker-override запускает их перед стартом Gunicorn.

## Подготовка

```bash
cp demo/.env.example demo/.env
```

В PowerShell:

```powershell
Copy-Item demo/.env.example demo/.env
```

Замените все значения с префиксом `replace-`. Файл `demo/.env` исключён из Git.

## Запуск

Linux/macOS:

```bash
./demo/start.sh
```

Windows PowerShell:

```powershell
.\demo\start.ps1
```

После запуска приложение доступно на `http://localhost:8000/`. Логины демонстрационных пользователей: `admin`, `security_officer`, `employee`, `employee2`; пароли берутся только из `demo/.env` и не хранятся в репозитории.

## Проверка и сброс

```bash
./demo/verify.sh
./demo/reset.sh
```

В PowerShell:

```powershell
.\demo\verify.ps1
.\demo\reset.ps1
```

Сброс удаляет volumes демонстрационного Compose-проекта, включая базу данных и загруженные файлы.
