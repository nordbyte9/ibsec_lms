from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class StaticDeliveryConfigurationTests(SimpleTestCase):
    def test_static_source_files_exist(self):
        required = (
            'css/design-system.css',
            'css/layout.css',
            'css/home-dashboard.css',
            'css/management-forms.css',
        )
        static_root = Path(settings.BASE_DIR) / 'static'
        for relative in required:
            with self.subTest(relative=relative):
                self.assertTrue((static_root / relative).is_file())

    def test_production_uses_versioned_static_files(self):
        settings_file = Path(settings.BASE_DIR) / 'ibsec_lms' / 'settings.py'
        if not settings_file.exists():
            settings_file = Path(settings.BASE_DIR) / 'config' / 'settings.py'
        source = settings_file.read_text(encoding='utf-8')
        self.assertIn('ManifestStaticFilesStorage', source)

    def test_docker_clears_and_recollects_static_files(self):
        entrypoint = (Path(settings.BASE_DIR) / 'docker' / 'entrypoint.sh').read_text(encoding='utf-8')
        self.assertIn('collectstatic --clear --noinput', entrypoint)
