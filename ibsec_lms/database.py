"""Database configuration helpers for IBSec LMS.

Priority:
1. DATABASE_URL;
2. DB_ENGINE=postgresql and DB_* variables;
3. SQLite fallback for local development.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping
from urllib.parse import parse_qsl, unquote, urlparse


class DatabaseConfigurationError(ValueError):
    """Raised when database environment variables are invalid or incomplete."""


_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}
_POSTGRES_ENGINES = {"postgres", "postgresql", "pgsql"}
_SQLITE_ENGINES = {"", "sqlite", "sqlite3"}


def _env_value(environ: Mapping[str, str], name: str, default: str = "") -> str:
    return environ.get(name, default).strip()


def _env_bool(environ: Mapping[str, str], name: str, default: bool) -> bool:
    raw_value = _env_value(environ, name)
    if not raw_value:
        return default

    normalized = raw_value.lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False

    raise DatabaseConfigurationError(
        f"{name} must be one of: true/false, 1/0, yes/no, on/off."
    )


def _env_non_negative_int(
    environ: Mapping[str, str],
    name: str,
    default: int,
) -> int:
    raw_value = _env_value(environ, name)
    if not raw_value:
        return default

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise DatabaseConfigurationError(f"{name} must be an integer.") from exc

    if value < 0:
        raise DatabaseConfigurationError(f"{name} must be zero or greater.")

    return value


def _postgres_connection_options(environ: Mapping[str, str]) -> dict[str, str]:
    options: dict[str, str] = {}
    sslmode = _env_value(environ, "DB_SSLMODE")
    if sslmode:
        options["sslmode"] = sslmode
    return options


def _postgres_config_from_url(
    database_url: str,
    environ: Mapping[str, str],
) -> dict[str, object]:
    parsed = urlparse(database_url)
    scheme = parsed.scheme.lower()

    if scheme not in _POSTGRES_ENGINES:
        raise DatabaseConfigurationError(
            "DATABASE_URL must use postgresql:// or postgres:// for IBSec LMS."
        )

    try:
        port = parsed.port or 5432
    except ValueError as exc:
        raise DatabaseConfigurationError("DATABASE_URL contains an invalid port.") from exc

    database_name = unquote(parsed.path.lstrip("/"))
    username = unquote(parsed.username or "")
    password = unquote(parsed.password or "")
    host = parsed.hostname or ""

    missing = []
    if not database_name:
        missing.append("database name")
    if not username:
        missing.append("username")
    if not password:
        missing.append("password")
    if not host:
        missing.append("host")

    if missing:
        raise DatabaseConfigurationError(
            "DATABASE_URL is incomplete; missing: " + ", ".join(missing) + "."
        )

    options = dict(parse_qsl(parsed.query, keep_blank_values=True))

    config: dict[str, object] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": database_name,
        "USER": username,
        "PASSWORD": password,
        "HOST": host,
        "PORT": str(port),
        "CONN_MAX_AGE": _env_non_negative_int(
            environ,
            "DB_CONN_MAX_AGE",
            default=60,
        ),
        "CONN_HEALTH_CHECKS": _env_bool(
            environ,
            "DB_CONN_HEALTH_CHECKS",
            default=True,
        ),
    }
    if options:
        config["OPTIONS"] = options
    return config


def _postgres_config_from_parts(environ: Mapping[str, str]) -> dict[str, object]:
    required_names = ("DB_NAME", "DB_USER", "DB_PASSWORD")
    missing = [name for name in required_names if not _env_value(environ, name)]
    if missing:
        raise DatabaseConfigurationError(
            "DB_ENGINE=postgresql requires: " + ", ".join(missing) + "."
        )

    port = _env_value(environ, "DB_PORT", "5432")
    try:
        port_number = int(port)
    except ValueError as exc:
        raise DatabaseConfigurationError("DB_PORT must be an integer.") from exc
    if not 1 <= port_number <= 65535:
        raise DatabaseConfigurationError("DB_PORT must be between 1 and 65535.")

    config: dict[str, object] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _env_value(environ, "DB_NAME"),
        "USER": _env_value(environ, "DB_USER"),
        "PASSWORD": _env_value(environ, "DB_PASSWORD"),
        "HOST": _env_value(environ, "DB_HOST", "localhost"),
        "PORT": str(port_number),
        "CONN_MAX_AGE": _env_non_negative_int(
            environ,
            "DB_CONN_MAX_AGE",
            default=60,
        ),
        "CONN_HEALTH_CHECKS": _env_bool(
            environ,
            "DB_CONN_HEALTH_CHECKS",
            default=True,
        ),
    }

    options = _postgres_connection_options(environ)
    if options:
        config["OPTIONS"] = options
    return config


def _sqlite_config(
    base_dir: Path,
    environ: Mapping[str, str],
) -> dict[str, object]:
    configured_path = _env_value(environ, "SQLITE_PATH", "db.sqlite3")
    sqlite_name: str | Path

    if configured_path == ":memory:":
        sqlite_name = configured_path
    else:
        candidate = Path(configured_path).expanduser()
        sqlite_name = candidate if candidate.is_absolute() else base_dir / candidate

    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": sqlite_name,
    }


def build_database_config(
    base_dir: Path,
    environ: Mapping[str, str] | None = None,
) -> dict[str, dict[str, object]]:
    """Build Django DATABASES with PostgreSQL priority and SQLite fallback."""

    current_environ = os.environ if environ is None else environ
    database_url = _env_value(current_environ, "DATABASE_URL")

    if database_url:
        default_config = _postgres_config_from_url(database_url, current_environ)
        return {"default": default_config}

    engine = _env_value(current_environ, "DB_ENGINE", "sqlite").lower()
    if engine in _POSTGRES_ENGINES:
        default_config = _postgres_config_from_parts(current_environ)
        return {"default": default_config}

    if engine in _SQLITE_ENGINES:
        default_config = _sqlite_config(base_dir, current_environ)
        return {"default": default_config}

    raise DatabaseConfigurationError(
        "Unsupported DB_ENGINE. Use 'postgresql' or 'sqlite'."
    )
