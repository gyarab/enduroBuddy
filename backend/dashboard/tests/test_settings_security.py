from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase


BACKEND_DIR = Path(__file__).resolve().parents[2]


class SettingsSecretKeySecurityTests(SimpleTestCase):
    def _run_settings_import(self, secret_key: str | None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.pop("DJANGO_SECRET_KEY", None)
        if secret_key is not None:
            env["DJANGO_SECRET_KEY"] = secret_key

        script = """
from pathlib import Path
import os
import sys

orig_exists = Path.exists
def patched_exists(self):
    if self.name == ".env":
        return False
    return orig_exists(self)

Path.exists = patched_exists
os.environ.pop("DJANGO_SECRET_KEY", None)
if len(sys.argv) > 1:
    os.environ["DJANGO_SECRET_KEY"] = sys.argv[1]

try:
    import config.settings as settings
except Exception as exc:
    print(type(exc).__name__)
    sys.exit(0)

print(settings.SECRET_KEY)
sys.exit(0)
"""

        args = [sys.executable, "-c", script]
        if secret_key is not None:
            args.append(secret_key)

        return subprocess.run(
            args,
            cwd=str(BACKEND_DIR),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_import_fails_without_secret_key(self):
        proc = self._run_settings_import(secret_key=None)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("ImproperlyConfigured", proc.stdout)

    def test_import_uses_environment_secret_key(self):
        key = "test-secret-key-123"
        proc = self._run_settings_import(secret_key=key)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), key)
