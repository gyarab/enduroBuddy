from __future__ import annotations

import tempfile
import shutil
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from activities.models import Activity, ActivityFile, ActivityInterval, ActivitySample

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "fit"


class FitImportAndCleanupTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username="admin", password="admin", email="a@a.cz")
        self.client.login(username="admin", password="admin")

    def _admin_upload_fit(self, fixture_name: str, expected_type: str):
        activity = Activity.objects.create(
            athlete=self.admin,
            started_at=timezone.now(),
            title="test",
        )

        fit_path = FIXTURES_DIR / fixture_name
        uploaded = SimpleUploadedFile(
            name=fit_path.name,
            content=fit_path.read_bytes(),
            content_type="application/octet-stream",
        )

        tmp_media = tempfile.mkdtemp()
        try:
            with override_settings(MEDIA_ROOT=tmp_media):
                url = reverse("admin:activities_activityfile_add")
                resp = self.client.post(
                    url,
                    data={
                        "activity": activity.id,
                        "file_type": ActivityFile.FileType.FIT,
                        "original_name": fit_path.name,
                        "file_upload": uploaded,  # musí sedět s tvým adminem
                    },
                    follow=True,
                )
                self.assertEqual(resp.status_code, 200)

                activity.refresh_from_db()
                self.assertEqual(activity.workout_type, expected_type)

                self.assertGreater(ActivityInterval.objects.filter(activity=activity).count(), 0)
                self.assertGreater(ActivitySample.objects.filter(activity=activity).count(), 100)

                af = ActivityFile.objects.latest("id")
                self.assertEqual(af.original_name, fit_path.name)
                self.assertFalse(af.file.name)  # file je "prázdný" (smazáno)

                # na disku nesmí zůstat žádný fit
                media_fits = list(Path(tmp_media).rglob("*.fit"))
                self.assertEqual(media_fits, [])
        finally:
            shutil.rmtree(tmp_media, ignore_errors=True)

    def test_easy_run_is_run_and_file_deleted(self):
        self._admin_upload_fit("Z3.fit", "RUN")

    def test_workout_is_workout_and_file_deleted(self):
        self._admin_upload_fit("2x1km, 4x500m.fit", "WORKOUT")
