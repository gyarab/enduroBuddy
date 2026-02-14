from __future__ import annotations

import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from activities.models import Activity, ActivityFile, ActivityInterval, ActivitySample


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "fit"


class AdminFitUploadTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(
            username="admin",
            password="admin",
            email="a@a.cz",
        )
        self.client.login(username="admin", password="admin")

    def _load_fixture(self, filename: str) -> SimpleUploadedFile:
        fit_path = FIXTURES_DIR / filename
        fit_bytes = fit_path.read_bytes()
        return SimpleUploadedFile(
            name=fit_path.name,
            content=fit_bytes,
            content_type="application/octet-stream",
        )

    def test_admin_upload_imports_fit_without_saving_to_media(self):
        # 1) vytvoř Activity
        activity = Activity.objects.create(
            athlete=self.admin,
            started_at=timezone.now(),
            title="test",
        )

        # 2) připrav upload (vyber fixture kterou fakt máš)
        uploaded = self._load_fixture("2x1km, 4x500m.fit")

        # 3) dočasný MEDIA_ROOT – testujeme, že se nic nevytvoří
        with tempfile.TemporaryDirectory() as tmp_media:
            with override_settings(MEDIA_ROOT=tmp_media):
                url = reverse("admin:activities_activityfile_add")

                # POZOR: klíč musí odpovídat field name v admin formu:
                # - pokud máš custom upload input: "file_upload"
                # - pokud používáš normální model FileField: "file"
                resp = self.client.post(
                    url,
                    data={
                        "activity": activity.id,
                        "file_type": ActivityFile.FileType.FIT,
                        "original_name": uploaded.name,
                        "file_upload": uploaded,
                    },
                    follow=True,
                )

                self.assertEqual(resp.status_code, 200)

                # 4) z DB musí být activity doplněná + timezone-aware
                activity.refresh_from_db()
                if activity.started_at is not None:
                    self.assertTrue(timezone.is_aware(activity.started_at))

                # 5) intervaly a samples musí vzniknout
                self.assertGreaterEqual(
                    ActivityInterval.objects.filter(activity=activity).count(),
                    1,
                )
                self.assertGreaterEqual(
                    ActivitySample.objects.filter(activity=activity).count(),
                    100,
                )

                # 6) ActivityFile se uloží jako "log", ale bez souboru na disku
                af = ActivityFile.objects.filter(activity=activity).latest("id")

                # FileField nikdy nebude None (je to FieldFile wrapper),
                # ale musí být prázdný (žádný název -> nic neukládáme).
                self.assertFalse(bool(af.file))
                self.assertEqual(af.file.name, "")
                self.assertEqual(af.original_name, uploaded.name)

                # 7) v MEDIA_ROOT nesmí vzniknout žádný .fit
                media_fits = list(Path(tmp_media).rglob("*.fit"))
                self.assertEqual(media_fits, [])
