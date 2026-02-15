from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import GarminConnection, GarminSyncAudit
from accounts.services.garmin_secret_store import encrypt_tokenstore
from activities.models import Activity, ActivityFile, ActivityInterval
from activities.services.garmin_importer import GarminDownloadResult, GarminFitPayload
from activities.services.fit_parser import parse_fit_file
from dashboard.views import _resolve_week_for_day
from training.models import CompletedTraining, PlannedTraining, TrainingMonth, TrainingWeek


FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "activities" / "tests" / "fixtures" / "fit"
TEST_KMS_KEY = "IO1tJrYVYrSgHUy4iJ5wsIXv89hRiYxYEyg2asOlVtE="


@override_settings(GARMIN_KMS_KEYS=TEST_KMS_KEY, GARMIN_KMS_KEY_ID="test-kms")
class DashboardFitImportTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="runner", password="runner")
        self.client.login(username="runner", password="runner")

    def _connect_garmin(self, tokenstore: str = "dummy-tokenstore"):
        return GarminConnection.objects.create(
            user=self.user,
            garmin_email="runner@example.com",
            garmin_display_name="runner",
            encrypted_tokenstore=encrypt_tokenstore(tokenstore),
            kms_key_id="test-kms",
            is_active=True,
        )

    def test_import_training_creates_or_assigns_planned_and_completed(self):
        fit_path = FIXTURES_DIR / "Z3.fit"
        fit_bytes = fit_path.read_bytes()
        parsed = parse_fit_file(BytesIO(fit_bytes))
        started_at = parsed.summary.get("started_at")
        self.assertIsNotNone(started_at)

        if timezone.is_naive(started_at):
            started_at = timezone.make_aware(started_at, timezone.get_current_timezone())
        run_day = timezone.localtime(started_at).date()

        resp = self.client.post(
            reverse("dashboard_home"),
            data={
                "fit_file": SimpleUploadedFile(
                    name=fit_path.name,
                    content=fit_bytes,
                    content_type="application/octet-stream",
                )
            },
        )

        self.assertEqual(resp.status_code, 302)

        month = TrainingMonth.objects.get(
            athlete=self.user,
            year=run_day.year,
            month=run_day.month,
        )
        self.assertIsNotNone(month)

        week = TrainingWeek.objects.get(training_month=month, planned_trainings__date=run_day)
        planned = PlannedTraining.objects.get(week=week, date=run_day)
        activity = Activity.objects.get(planned_training=planned, athlete=self.user)
        completed = CompletedTraining.objects.get(planned=planned)

        self.assertEqual(completed.activity_id, activity.id)
        self.assertIsNotNone(completed.time_seconds)
        self.assertIsNotNone(completed.distance_m)
        self.assertEqual(completed.distance_m, activity.distance_m)

    def test_import_training_skips_duplicate_file(self):
        fit_path = FIXTURES_DIR / "Z3.fit"
        fit_bytes = fit_path.read_bytes()

        payload = {
            "fit_file": SimpleUploadedFile(
                name=fit_path.name,
                content=fit_bytes,
                content_type="application/octet-stream",
            )
        }
        resp1 = self.client.post(reverse("dashboard_home"), data=payload)
        self.assertEqual(resp1.status_code, 302)

        payload2 = {
            "fit_file": SimpleUploadedFile(
                name=fit_path.name,
                content=fit_bytes,
                content_type="application/octet-stream",
            )
        }
        resp2 = self.client.post(reverse("dashboard_home"), data=payload2)
        self.assertEqual(resp2.status_code, 302)

        self.assertEqual(Activity.objects.filter(athlete=self.user).count(), 1)
        self.assertEqual(ActivityFile.objects.filter(activity__athlete=self.user).count(), 1)
        self.assertEqual(CompletedTraining.objects.filter(planned__week__training_month__athlete=self.user).count(), 1)

    def test_custom_week_boundaries_follow_monday_start_rule(self):
        w_feb_23 = _resolve_week_for_day(self.user, timezone.datetime(2026, 2, 23).date())
        w_mar_1 = _resolve_week_for_day(self.user, timezone.datetime(2026, 3, 1).date())
        self.assertEqual(w_feb_23.training_month.year, 2026)
        self.assertEqual(w_feb_23.training_month.month, 2)
        self.assertEqual(w_feb_23.week_index, 4)
        self.assertEqual(w_mar_1.training_month.year, 2026)
        self.assertEqual(w_mar_1.training_month.month, 2)
        self.assertEqual(w_mar_1.week_index, 4)

        w_mar_2 = _resolve_week_for_day(self.user, timezone.datetime(2026, 3, 2).date())
        w_mar_30 = _resolve_week_for_day(self.user, timezone.datetime(2026, 3, 30).date())
        w_apr_5 = _resolve_week_for_day(self.user, timezone.datetime(2026, 4, 5).date())
        self.assertEqual(w_mar_2.training_month.year, 2026)
        self.assertEqual(w_mar_2.training_month.month, 3)
        self.assertEqual(w_mar_2.week_index, 1)
        self.assertEqual(w_mar_30.training_month.year, 2026)
        self.assertEqual(w_mar_30.training_month.month, 3)
        self.assertEqual(w_mar_30.week_index, 5)
        self.assertEqual(w_apr_5.training_month.year, 2026)
        self.assertEqual(w_apr_5.training_month.month, 3)
        self.assertEqual(w_apr_5.week_index, 5)

        march_weeks = TrainingWeek.objects.filter(
            training_month__athlete=self.user,
            training_month__year=2026,
            training_month__month=3,
        ).order_by("week_index")
        self.assertEqual(list(march_weeks.values_list("week_index", flat=True)), [1, 5])

    def test_completed_rows_are_aggregated_by_day_and_sorted_by_activity_start(self):
        run_day = date(2026, 3, 3)
        week = _resolve_week_for_day(self.user, run_day)

        p1 = PlannedTraining.objects.create(week=week, date=run_day, day_label="Tue", title="Warmup", order_in_day=1)
        p2 = PlannedTraining.objects.create(week=week, date=run_day, day_label="Tue", title="Workout", order_in_day=2)
        p3 = PlannedTraining.objects.create(week=week, date=run_day, day_label="Tue", title="Cooldown", order_in_day=3)

        tz = timezone.get_current_timezone()
        Activity.objects.create(
            athlete=self.user,
            planned_training=p1,
            workout_type=Activity.WorkoutType.RUN,
            started_at=timezone.make_aware(timezone.datetime(2026, 3, 3, 8, 0, 0), tz),
            distance_m=2000,
            duration_s=600,
            avg_pace_s_per_km=300,
            avg_hr=140,
            max_hr=152,
        )
        a2 = Activity.objects.create(
            athlete=self.user,
            planned_training=p2,
            workout_type=Activity.WorkoutType.WORKOUT,
            started_at=timezone.make_aware(timezone.datetime(2026, 3, 3, 9, 0, 0), tz),
            distance_m=6000,
            duration_s=1800,
            avg_hr=165,
            max_hr=182,
        )
        Activity.objects.create(
            athlete=self.user,
            planned_training=p3,
            workout_type=Activity.WorkoutType.RUN,
            started_at=timezone.make_aware(timezone.datetime(2026, 3, 3, 10, 0, 0), tz),
            distance_m=2000,
            duration_s=600,
            avg_pace_s_per_km=320,
            avg_hr=145,
            max_hr=155,
        )

        ActivityInterval.objects.create(activity=a2, index=1, duration_s=60, distance_m=400, avg_hr=170, max_hr=180)
        ActivityInterval.objects.create(activity=a2, index=2, duration_s=100, distance_m=500, avg_hr=172, max_hr=182)

        resp = self.client.get(reverse("dashboard_home"))
        self.assertEqual(resp.status_code, 200)

        month_cards = resp.context["month_cards"]
        self.assertEqual(len(month_cards), 1)
        weeks = month_cards[0]["weeks"]
        self.assertEqual(len(weeks), 1)
        planned_rows = weeks[0].planned_rows
        self.assertEqual(len(planned_rows), 1)
        self.assertEqual(planned_rows[0]["title"], "Warmup | Workout | Cooldown")
        rows = weeks[0].completed_rows
        self.assertEqual(len(rows), 1)

        row = rows[0]
        self.assertEqual(row["km"], "10.00")
        self.assertEqual(row["min"], "50")
        self.assertEqual(row["third"], "5:00/km | (1:00, 1:40) | 5:20/km")

    def test_two_phase_day_renders_two_rows_in_planned_and_completed(self):
        run_day = date(2026, 3, 4)
        week = _resolve_week_for_day(self.user, run_day)
        tz = timezone.get_current_timezone()

        p1 = PlannedTraining.objects.create(
            week=week,
            date=run_day,
            day_label="Wed",
            title="Morning run",
            order_in_day=1,
            is_two_phase_day=True,
        )
        p2 = PlannedTraining.objects.create(
            week=week,
            date=run_day,
            day_label="Wed",
            title="Evening workout",
            order_in_day=2,
            is_two_phase_day=True,
        )

        Activity.objects.create(
            athlete=self.user,
            planned_training=p1,
            workout_type=Activity.WorkoutType.RUN,
            started_at=timezone.make_aware(timezone.datetime(2026, 3, 4, 7, 0, 0), tz),
            distance_m=3000,
            duration_s=900,
            avg_pace_s_per_km=300,
            avg_hr=140,
            max_hr=150,
        )
        a2 = Activity.objects.create(
            athlete=self.user,
            planned_training=p2,
            workout_type=Activity.WorkoutType.WORKOUT,
            started_at=timezone.make_aware(timezone.datetime(2026, 3, 4, 18, 0, 0), tz),
            distance_m=5000,
            duration_s=1500,
            avg_hr=165,
            max_hr=180,
        )
        ActivityInterval.objects.create(activity=a2, index=1, duration_s=60, distance_m=400, avg_hr=170, max_hr=178)
        ActivityInterval.objects.create(activity=a2, index=2, duration_s=80, distance_m=500, avg_hr=172, max_hr=180)

        resp = self.client.get(reverse("dashboard_home"))
        self.assertEqual(resp.status_code, 200)

        week_ctx = resp.context["month_cards"][0]["weeks"][0]
        planned_rows = week_ctx.planned_rows
        completed_rows = week_ctx.completed_rows

        self.assertEqual(len(planned_rows), 2)
        self.assertEqual(planned_rows[0]["title"], "Morning run")
        self.assertEqual(planned_rows[1]["title"], "Evening workout")
        self.assertIsNone(planned_rows[1]["date"])
        self.assertEqual(planned_rows[1]["day_label"], "")

        self.assertEqual(len(completed_rows), 2)
        self.assertEqual(completed_rows[0]["km"], "3.00")
        self.assertEqual(completed_rows[0]["third"], "5:00/km")
        self.assertEqual(completed_rows[1]["km"], "5.00")
        self.assertEqual(completed_rows[1]["third"], "(1:00, 1:20)")

    @patch("dashboard.services.imports.download_garmin_fit_payloads")
    def test_garmin_sync_imports_activity(self, mocked_download):
        fit_path = FIXTURES_DIR / "Z3.fit"
        fit_bytes = fit_path.read_bytes()
        self._connect_garmin()
        mocked_download.return_value = GarminDownloadResult(
            payloads=[GarminFitPayload(activity_id="1001", original_name="garmin_1001.fit", fit_bytes=fit_bytes)],
            refreshed_tokenstore="new-token",
        )

        resp = self.client.post(reverse("dashboard_home"), data={"import_source": "garmin_sync"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Activity.objects.filter(athlete=self.user).count(), 1)
        self.assertEqual(ActivityFile.objects.filter(activity__athlete=self.user).count(), 1)
        self.assertEqual(CompletedTraining.objects.filter(planned__week__training_month__athlete=self.user).count(), 1)

    @patch("dashboard.services.imports.download_garmin_fit_payloads")
    def test_garmin_sync_skips_duplicates(self, mocked_download):
        fit_path = FIXTURES_DIR / "Z3.fit"
        fit_bytes = fit_path.read_bytes()
        payload = GarminFitPayload(activity_id="1001", original_name="garmin_1001.fit", fit_bytes=fit_bytes)
        self._connect_garmin()
        mocked_download.return_value = GarminDownloadResult(
            payloads=[payload, payload],
            refreshed_tokenstore="new-token",
        )

        resp = self.client.post(reverse("dashboard_home"), data={"import_source": "garmin_sync"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Activity.objects.filter(athlete=self.user).count(), 1)
        self.assertEqual(ActivityFile.objects.filter(activity__athlete=self.user).count(), 1)

    @patch("dashboard.services.imports.download_garmin_fit_payloads")
    def test_garmin_sync_uses_selected_range(self, mocked_download):
        self._connect_garmin()
        mocked_download.return_value = GarminDownloadResult(payloads=[], refreshed_tokenstore="new-token")

        resp = self.client.post(
            reverse("dashboard_home"),
            data={"import_source": "garmin_sync", "garmin_range": "yesterday"},
        )
        self.assertEqual(resp.status_code, 302)
        kwargs = mocked_download.call_args.kwargs
        self.assertIn("from_day", kwargs)
        self.assertIn("to_day", kwargs)
        self.assertEqual(kwargs["from_day"], kwargs["to_day"])

    @patch("dashboard.services.imports.connect_garmin_account")
    def test_garmin_connect_persists_encrypted_tokens_and_audit(self, mocked_connect):
        mocked_connect.return_value = type(
            "Bundle",
            (),
            {"tokenstore": "token-value", "display_name": "Runner Name", "full_name": "Runner Name"},
        )()

        resp = self.client.post(
            reverse("dashboard_home"),
            data={
                "import_source": "garmin_connect",
                "garmin_email": "runner@example.com",
                "garmin_password": "secret",
            },
        )
        self.assertEqual(resp.status_code, 302)
        conn = GarminConnection.objects.get(user=self.user)
        self.assertTrue(conn.encrypted_tokenstore)
        self.assertNotEqual(conn.encrypted_tokenstore, "token-value")
        self.assertEqual(conn.garmin_email, "runner@example.com")
        self.assertEqual(conn.garmin_display_name, "Runner Name")
        self.assertTrue(
            GarminSyncAudit.objects.filter(
                user=self.user,
                action=GarminSyncAudit.Action.CONNECT,
                status=GarminSyncAudit.Status.SUCCESS,
            ).exists()
        )

    def test_garmin_revoke_disables_connection_and_creates_audit(self):
        conn = self._connect_garmin()

        resp = self.client.post(reverse("dashboard_home"), data={"import_source": "garmin_revoke"})
        self.assertEqual(resp.status_code, 302)

        conn.refresh_from_db()
        self.assertFalse(conn.is_active)
        self.assertEqual(conn.encrypted_tokenstore, "")
        self.assertIsNotNone(conn.revoked_at)
        self.assertTrue(
            GarminSyncAudit.objects.filter(
                user=self.user,
                action=GarminSyncAudit.Action.REVOKE,
                status=GarminSyncAudit.Status.SUCCESS,
            ).exists()
        )
