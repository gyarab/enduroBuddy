from __future__ import annotations

from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from activities.models import Activity, ActivityFile, ActivityInterval, ActivitySample
from activities.services.fit_importer import import_fit_into_activity
from training.models import PlannedTraining, TrainingMonth, TrainingWeek

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "fit"


class FitImportServiceTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="t", password="t")

    def _import(self, fixture_name: str) -> Activity:
        activity = Activity.objects.create(
            athlete=self.user,
            started_at=timezone.now(),
            title="test",
        )

        fit_path = FIXTURES_DIR / fixture_name
        with open(fit_path, "rb") as f:
            outcome = import_fit_into_activity(
        activity=activity,
        fileobj=f,
        original_name=fit_path.name,
        create_activity_file_row=False,
        )

        outcome.activity.refresh_from_db()
        return outcome.activity


    def test_easy_run_import(self):
        activity = self._import("Z3.fit")

        self.assertEqual(activity.workout_type, "RUN")
        self.assertIsNotNone(activity.distance_m)
        self.assertIsNotNone(activity.duration_s)

        self.assertGreater(ActivitySample.objects.filter(activity=activity).count(), 100)
        # u easy běhu intervaly můžou být autolapy, ale aspoň něco by mělo vzniknout
        self.assertGreater(ActivityInterval.objects.filter(activity=activity).count(), 1)

    def test_workout_import(self):
        activity = self._import("2x1km, 4x500m.fit")

        self.assertEqual(activity.workout_type, "WORKOUT")

        intervals = ActivityInterval.objects.filter(activity=activity).order_by("index")
        self.assertGreaterEqual(intervals.count(), 4)

        paces = [it.avg_pace_s_per_km for it in intervals if it.avg_pace_s_per_km is not None]
        self.assertGreaterEqual(len(paces), 4)

        self.assertGreater(ActivitySample.objects.filter(activity=activity).count(), 100)

    def test_import_with_planned_training_and_activity_file_row(self):
        month = TrainingMonth.objects.create(
            athlete=self.user,
            year=2026,
            month=1,
        )
        week = TrainingWeek.objects.create(
            training_month=month,
            week_index=1,
        )
        planned = PlannedTraining.objects.create(
            week=week,
            day_label="Mon",
            title="Easy run",
            order_in_day=1,
        )
        activity = Activity.objects.create(
            athlete=self.user,
            planned_training=planned,
            started_at=timezone.now(),
            title="planned-session",
        )

        fit_path = FIXTURES_DIR / "Z3.fit"
        with open(fit_path, "rb") as f:
            outcome = import_fit_into_activity(
                activity=activity,
                fileobj=f,
                original_name=fit_path.name,
                create_activity_file_row=True,
            )

        outcome.activity.refresh_from_db()
        self.assertEqual(outcome.activity.planned_training_id, planned.id)
        self.assertEqual(outcome.activity.workout_type, "RUN")
        self.assertIsNotNone(outcome.activity.duration_s)
        self.assertIsNotNone(outcome.activity.distance_m)
        self.assertGreater(ActivityInterval.objects.filter(activity=outcome.activity).count(), 0)
        self.assertGreater(ActivitySample.objects.filter(activity=outcome.activity).count(), 100)

        af = ActivityFile.objects.get(activity=outcome.activity)
        self.assertEqual(af.file_type, ActivityFile.FileType.FIT)
        self.assertEqual(af.original_name, fit_path.name)
        self.assertFalse(bool(af.file))
