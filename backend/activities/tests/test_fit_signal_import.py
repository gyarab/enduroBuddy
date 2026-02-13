from __future__ import annotations

from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.base import File
from django.test import TestCase
from django.utils import timezone

from activities.models import Activity, ActivityFile, ActivityInterval


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "fit"


class FitImportSignalTests(TestCase):
    def test_upload_fit_creates_intervals_and_sets_workout_type(self):
        User = get_user_model()
        user = User.objects.create_user(username="t", password="t")

        activity = Activity.objects.create(
            athlete=user,
            started_at=timezone.now(),
            title="test",
        )

        fit_path = FIXTURES_DIR / "2x1km, 4x500m.fit"
        with open(fit_path, "rb") as f:
            django_file = File(f, name=fit_path.name)
            ActivityFile.objects.create(
                activity=activity,
                file_type=ActivityFile.FileType.FIT,
                file=django_file,
                original_name=fit_path.name,
            )

        activity.refresh_from_db()

        self.assertEqual(activity.workout_type, "WORKOUT")
        self.assertTrue(ActivityInterval.objects.filter(activity=activity).count() >= 4)
