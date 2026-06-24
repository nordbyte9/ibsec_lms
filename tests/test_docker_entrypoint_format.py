from pathlib import Path

from django.test import SimpleTestCase


class DockerEntrypointFormatTests(SimpleTestCase):
    def test_entrypoint_uses_unix_line_endings(self):
        root = Path(__file__).resolve().parents[1]
        for relative_path in ('docker/entrypoint.sh', 'demo/start-web.sh'):
            path = root / relative_path
            data = path.read_bytes()
            self.assertTrue(data.startswith(b'#!/bin/sh\n'), relative_path)
            self.assertNotIn(b'\r\n', data, relative_path)

    def test_project_enforces_lf_for_shell_scripts(self):
        root = Path(__file__).resolve().parents[1]
        attributes = (root / '.gitattributes').read_text(encoding='utf-8')
        self.assertIn('*.sh text eol=lf', attributes)

        dockerfile = root / 'Dockerfile'
        if not dockerfile.exists():
            dockerfile = root / 'docker' / 'Dockerfile'
        text = dockerfile.read_text(encoding='utf-8')
        self.assertIn('# Normalize shell scripts copied from Windows.', text)
        self.assertIn("sed -i 's/\\r$//'", text)
        self.assertIn('chmod +x /app/docker/entrypoint.sh', text)
