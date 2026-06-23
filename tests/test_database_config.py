from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ibsec_lms.database import (
    DatabaseConfigurationError,
    build_database_config,
)


class DatabaseConfigurationTests(TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_sqlite_is_used_by_default(self):
        database = build_database_config(self.base_dir, {})['default']

        self.assertEqual(database['ENGINE'], 'django.db.backends.sqlite3')
        self.assertEqual(database['NAME'], self.base_dir / 'db.sqlite3')

    def test_relative_sqlite_path_is_resolved_from_base_dir(self):
        database = build_database_config(
            self.base_dir,
            {'DB_ENGINE': 'sqlite', 'SQLITE_PATH': 'instance/local.sqlite3'},
        )['default']

        self.assertEqual(database['NAME'], self.base_dir / 'instance/local.sqlite3')

    def test_postgresql_is_built_from_db_variables(self):
        database = build_database_config(
            self.base_dir,
            {
                'DB_ENGINE': 'postgresql',
                'DB_HOST': 'db.internal',
                'DB_PORT': '5433',
                'DB_NAME': 'ibsec_lms',
                'DB_USER': 'ibsec_user',
                'DB_PASSWORD': 'secret',
                'DB_SSLMODE': 'require',
                'DB_CONN_MAX_AGE': '120',
                'DB_CONN_HEALTH_CHECKS': 'true',
            },
        )['default']

        self.assertEqual(database['ENGINE'], 'django.db.backends.postgresql')
        self.assertEqual(database['HOST'], 'db.internal')
        self.assertEqual(database['PORT'], '5433')
        self.assertEqual(database['NAME'], 'ibsec_lms')
        self.assertEqual(database['USER'], 'ibsec_user')
        self.assertEqual(database['PASSWORD'], 'secret')
        self.assertEqual(database['CONN_MAX_AGE'], 120)
        self.assertTrue(database['CONN_HEALTH_CHECKS'])
        self.assertEqual(database['OPTIONS'], {'sslmode': 'require'})

    def test_database_url_has_priority_over_db_parts(self):
        database = build_database_config(
            self.base_dir,
            {
                'DATABASE_URL': (
                    'postgresql://url_user:url%20password@db.example:5544/'
                    'url_database?sslmode=require'
                ),
                'DB_ENGINE': 'sqlite',
                'DB_NAME': 'ignored',
            },
        )['default']

        self.assertEqual(database['ENGINE'], 'django.db.backends.postgresql')
        self.assertEqual(database['NAME'], 'url_database')
        self.assertEqual(database['USER'], 'url_user')
        self.assertEqual(database['PASSWORD'], 'url password')
        self.assertEqual(database['HOST'], 'db.example')
        self.assertEqual(database['PORT'], '5544')
        self.assertEqual(database['OPTIONS'], {'sslmode': 'require'})

    def test_missing_postgresql_variables_fail_fast(self):
        with self.assertRaisesRegex(
            DatabaseConfigurationError,
            'DB_NAME, DB_USER, DB_PASSWORD',
        ):
            build_database_config(
                self.base_dir,
                {'DB_ENGINE': 'postgresql'},
            )

    def test_unsupported_engine_fails_instead_of_silent_sqlite_fallback(self):
        with self.assertRaisesRegex(DatabaseConfigurationError, 'Unsupported DB_ENGINE'):
            build_database_config(
                self.base_dir,
                {'DB_ENGINE': 'postgreql'},
            )

    def test_invalid_database_url_scheme_is_rejected(self):
        with self.assertRaisesRegex(DatabaseConfigurationError, 'postgresql://'):
            build_database_config(
                self.base_dir,
                {'DATABASE_URL': 'mysql://user:password@localhost/database'},
            )
