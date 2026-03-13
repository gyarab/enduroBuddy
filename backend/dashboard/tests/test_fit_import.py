from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import GarminConnection, GarminSyncAudit, ImportJob
from accounts.services.garmin_secret_store import encrypt_tokenstore
from activities.models import Activity, ActivityFile, ActivityImportLedger, ActivityInterval
from activities.services.garmin_importer import GarminDownloadResult, GarminFitPayload
from activities.services.fit_parser import parse_fit_file
from dashboard.services.imports import _resolve_planned_training
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

    @override_settings(DEBUG=True)
    def test_dashboard_can_render_test_notifications_from_query_param(self):
        resp = self.client.get(reverse("dashboard_home"), {"test_notifications": "1"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Test: Novy treninkovy plan je pripraven.")
        self.assertContains(resp, "Test: Garmin synchronizace bude spustena za chvili.")

    def test_import_job_status_returns_progress_fields(self):
        job = ImportJob.objects.create(
            user=self.user,
            kind=ImportJob.Kind.GARMIN_SYNC,
            status=ImportJob.Status.RUNNING,
            message="Garmin sync: processing 2/4 (52%).",
            total_count=4,
            processed_count=2,
            imported_count=1,
            skipped_count=1,
        )

        resp = self.client.get(reverse("import_job_status", kwargs={"job_id": job.id}))
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["job"]["status"], ImportJob.Status.RUNNING)
        self.assertEqual(payload["job"]["status_label"], "Running")
        self.assertEqual(payload["job"]["progress_percent"], 50)
        self.assertEqual(payload["job"]["total_count"], 4)
        self.assertEqual(payload["job"]["processed_count"], 2)

    @override_settings(DEBUG=True)
    def test_test_garmin_import_query_cleans_admin_week_and_completed(self):
        User = get_user_model()
        admin = User.objects.create_user(username="admin", password="admin")
        self.client.login(username="admin", password="admin")

        year = timezone.localdate().year
        run_day = date(year, 3, 4)
        week = _resolve_week_for_day(admin, run_day)
        planned = PlannedTraining.objects.create(
            week=week,
            date=run_day,
            day_label="Wed",
            title="Test run",
            order_in_day=1,
        )
        activity = Activity.objects.create(
            athlete=admin,
            planned_training=planned,
            started_at=timezone.make_aware(timezone.datetime(year, 3, 4, 8, 0, 0), timezone.get_current_timezone()),
            title="Imported test",
        )
        CompletedTraining.objects.create(planned=planned, activity=activity, time_seconds=600, distance_m=2000)
        ActivityImportLedger.objects.create(athlete=admin, checksum_sha256="a" * 64)

        resp = self.client.get(reverse("dashboard_home"), {"test_garmin_import": "1"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("dashboard_home"))

        self.assertFalse(PlannedTraining.objects.filter(id=planned.id).exists())
        self.assertFalse(CompletedTraining.objects.filter(planned_id=planned.id).exists())
        self.assertFalse(Activity.objects.filter(id=activity.id).exists())
        self.assertEqual(ActivityImportLedger.objects.filter(athlete=admin).count(), 0)
        self.assertTrue(
            TrainingWeek.objects.filter(
                training_month__athlete=admin,
                training_month__year=year,
                training_month__month=3,
                week_index=1,
            ).exists()
        )
        self.assertEqual(
            PlannedTraining.objects.filter(
                week__training_month__athlete=admin,
                date__range=(date(year, 3, 2), date(year, 3, 8)),
                order_in_day=1,
            ).count(),
            7,
        )

    @override_settings(DEBUG=True)
    def test_remove_week_completed_query_cleans_only_completed_for_selected_admin_week(self):
        User = get_user_model()
        admin = User.objects.create_user(username="admin", password="admin")
        self.client.login(username="admin", password="admin")

        week = _resolve_week_for_day(admin, date(2026, 3, 4))
        target = PlannedTraining.objects.create(
            week=week,
            date=date(2026, 3, 4),
            day_label="Wed",
            title="Target run",
            order_in_day=1,
        )
        keep = PlannedTraining.objects.create(
            week=week,
            date=date(2026, 3, 5),
            day_label="Thu",
            title="Keep row",
            order_in_day=1,
        )
        target_activity = Activity.objects.create(
            athlete=admin,
            planned_training=target,
            started_at=timezone.make_aware(timezone.datetime(2026, 3, 4, 8, 0, 0), timezone.get_current_timezone()),
            title="Imported target",
        )
        keep_activity = Activity.objects.create(
            athlete=admin,
            planned_training=keep,
            started_at=timezone.make_aware(timezone.datetime(2026, 3, 5, 8, 0, 0), timezone.get_current_timezone()),
            title="Imported keep",
        )
        CompletedTraining.objects.create(planned=target, activity=target_activity, time_seconds=600, distance_m=2000)
        CompletedTraining.objects.create(planned=keep, activity=keep_activity, time_seconds=1200, distance_m=4000)

        resp = self.client.get(reverse("dashboard_home"), {"remove_week_completed": "3/1"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("dashboard_home"))

        self.assertTrue(PlannedTraining.objects.filter(id=target.id).exists())
        self.assertTrue(PlannedTraining.objects.filter(id=keep.id).exists())
        self.assertFalse(CompletedTraining.objects.filter(planned_id=target.id).exists())
        self.assertFalse(CompletedTraining.objects.filter(planned_id=keep.id).exists())
        self.assertFalse(Activity.objects.filter(id=target_activity.id).exists())
        self.assertFalse(Activity.objects.filter(id=keep_activity.id).exists())

    def test_completed_rows_are_aggregated_by_day_and_sorted_by_activity_start(self):
        run_day = date(2026, 3, 3)
        week = _resolve_week_for_day(self.user, run_day)

        p1 = PlannedTraining.objects.create(week=week, date=run_day, day_label="Tue", title="Warmup", order_in_day=1)
        p2 = PlannedTraining.objects.create(
            week=week,
            date=run_day,
            day_label="Tue",
            title="Workout",
            session_type=PlannedTraining.SessionType.WORKOUT,
            order_in_day=2,
        )
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
            session_type=PlannedTraining.SessionType.WORKOUT,
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
            avg_pace_s_per_km=295,
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
        self.assertEqual(completed_rows[0]["min"], "15")
        self.assertEqual(completed_rows[0]["third"], "5:00/km")
        self.assertEqual(completed_rows[1]["km"], "8.00")
        self.assertEqual(completed_rows[1]["min"], "40")
        self.assertEqual(completed_rows[1]["third"], "(1:00, 1:20), 4:55/km")
        self.assertEqual(week_ctx.completed_total["km"], "8.00")
        self.assertEqual(week_ctx.completed_total["time"], "40")

    def test_import_resolver_marks_day_as_two_phase_when_creating_second_training(self):
        run_day = date(2026, 3, 6)
        week = _resolve_week_for_day(self.user, run_day)
        first = PlannedTraining.objects.create(
            week=week,
            date=run_day,
            day_label="Fri",
            title="AM run",
            order_in_day=1,
            is_two_phase_day=False,
        )
        Activity.objects.create(
            athlete=self.user,
            planned_training=first,
            workout_type=Activity.WorkoutType.RUN,
            started_at=timezone.now(),
            distance_m=5000,
            duration_s=1500,
        )

        second = _resolve_planned_training(self.user, run_day, "PM run")
        first.refresh_from_db()
        second.refresh_from_db()

        self.assertNotEqual(first.id, second.id)
        self.assertEqual(second.order_in_day, 2)
        self.assertTrue(first.is_two_phase_day)
        self.assertTrue(second.is_two_phase_day)

    def test_planned_training_session_type_can_be_updated(self):
        run_day = date(2026, 3, 7)
        week = _resolve_week_for_day(self.user, run_day)
        planned = PlannedTraining.objects.create(
            week=week,
            date=run_day,
            day_label="Sat",
            title="8 km klus",
            session_type=PlannedTraining.SessionType.RUN,
            order_in_day=1,
        )

        resp = self.client.post(
            reverse("athlete_update_planned_training"),
            data='{"planned_id": %d, "field": "session_type", "value": "WORKOUT"}' % planned.id,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        planned.refresh_from_db()
        self.assertEqual(planned.session_type, PlannedTraining.SessionType.WORKOUT)

    def test_plan_text_drives_run_vs_workout_rendering(self):
        tz = timezone.get_current_timezone()
        week = _resolve_week_for_day(self.user, date(2026, 3, 10))

        planned_workout = PlannedTraining.objects.create(
            week=week,
            date=date(2026, 3, 10),
            day_label="Tue",
            title="3x(500-300-200), P=60s",
            session_type=PlannedTraining.SessionType.WORKOUT,
            order_in_day=1,
        )
        activity_workout_like = Activity.objects.create(
            athlete=self.user,
            planned_training=planned_workout,
            workout_type=Activity.WorkoutType.RUN,
            started_at=timezone.make_aware(timezone.datetime(2026, 3, 10, 8, 0, 0), tz),
            distance_m=7000,
            duration_s=2100,
            avg_pace_s_per_km=300,
        )
        ActivityInterval.objects.create(activity=activity_workout_like, index=1, duration_s=99, distance_m=500)
        ActivityInterval.objects.create(activity=activity_workout_like, index=2, duration_s=56, distance_m=300)
        ActivityInterval.objects.create(activity=activity_workout_like, index=3, duration_s=35, distance_m=200)

        planned_run = PlannedTraining.objects.create(
            week=week,
            date=date(2026, 3, 11),
            day_label="Wed",
            title="8 km klus",
            session_type=PlannedTraining.SessionType.RUN,
            order_in_day=1,
        )
        activity_run_like = Activity.objects.create(
            athlete=self.user,
            planned_training=planned_run,
            workout_type=Activity.WorkoutType.WORKOUT,
            started_at=timezone.make_aware(timezone.datetime(2026, 3, 11, 8, 0, 0), tz),
            distance_m=8000,
            duration_s=2400,
            avg_pace_s_per_km=300,
        )
        ActivityInterval.objects.create(activity=activity_run_like, index=1, duration_s=100, distance_m=400)

        resp = self.client.get(reverse("dashboard_home"))
        self.assertEqual(resp.status_code, 200)

        week_ctx = resp.context["month_cards"][0]["weeks"][0]
        rows = week_ctx.completed_rows
        self.assertGreaterEqual(len(rows), 2)
        self.assertEqual(rows[0]["third"], "(1:39, 56, 35), 5:00/km")
        self.assertEqual(rows[1]["third"], "5:00/km")

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

    def test_dashboard_renders_week_garmin_sync_button_for_connected_account(self):
        self._connect_garmin()
        week = _resolve_week_for_day(self.user, date(2026, 3, 2))
        PlannedTraining.objects.create(
            week=week,
            date=date(2026, 3, 2),
            day_label="Mon",
            title="Easy run",
            order_in_day=1,
        )

        resp = self.client.get(reverse("dashboard_home"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "eb-garmin-week-sync-btn")
        self.assertContains(resp, "data-garmin-week-sync-url")
        self.assertContains(resp, reverse("garmin_sync_week"))

    @override_settings(USE_TZ=True)
    @patch("dashboard.services.month_cards.timezone.localdate")
    def test_dashboard_disables_week_garmin_sync_for_future_week(self, mocked_localdate):
        mocked_localdate.return_value = date(2026, 3, 1)
        self._connect_garmin()
        week = _resolve_week_for_day(self.user, date(2026, 3, 2))
        PlannedTraining.objects.create(
            week=week,
            date=date(2026, 3, 2),
            day_label="Mon",
            title="Easy run",
            order_in_day=1,
        )

        resp = self.client.get(reverse("dashboard_home"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Tento tyden jeste nezacal.")
        self.assertContains(resp, "eb-garmin-week-sync-btn")
        self.assertContains(resp, "disabled")

    @patch("dashboard.services.imports.download_garmin_fit_payloads")
    def test_garmin_week_sync_replaces_only_days_with_new_payloads(self, mocked_download):
        fit_path = FIXTURES_DIR / "Z3.fit"
        fit_bytes = fit_path.read_bytes()
        parsed = parse_fit_file(BytesIO(fit_bytes))
        started_at = parsed.summary.get("started_at")
        self.assertIsNotNone(started_at)
        if timezone.is_naive(started_at):
            started_at = timezone.make_aware(started_at, timezone.get_current_timezone())
        run_day = timezone.localtime(started_at).date()
        week = _resolve_week_for_day(self.user, run_day)
        other_day = run_day + timedelta(days=1)

        target = PlannedTraining.objects.create(
            week=week,
            date=run_day,
            day_label="Run",
            title="Target",
            order_in_day=1,
        )
        untouched = PlannedTraining.objects.create(
            week=week,
            date=other_day,
            day_label="Keep",
            title="Keep",
            order_in_day=1,
        )
        CompletedTraining.objects.create(
            planned=target,
            time_seconds=111,
            distance_m=2222,
            avg_hr=123,
            note="manual target",
            feel="199",
        )
        CompletedTraining.objects.create(
            planned=untouched,
            time_seconds=333,
            distance_m=4444,
            avg_hr=145,
            note="manual keep",
            feel="188",
        )

        self._connect_garmin()
        mocked_download.return_value = GarminDownloadResult(
            payloads=[GarminFitPayload(activity_id="1001", original_name="garmin_1001.fit", fit_bytes=fit_bytes)],
            refreshed_tokenstore="new-token",
        )

        week_start = run_day - timedelta(days=run_day.weekday())
        resp = self.client.post(
            reverse("garmin_sync_week"),
            data={"week_start": week_start.isoformat()},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["replaced_count"], 1)

        target.refresh_from_db()
        untouched.refresh_from_db()
        target_completed = CompletedTraining.objects.get(planned=target)
        untouched_completed = CompletedTraining.objects.get(planned=untouched)

        target_activity = Activity.objects.get(planned_training=target)
        self.assertEqual(target_completed.activity_id, target_activity.id)
        self.assertEqual(target_completed.distance_m, int(parsed.summary.get("distance_m") or 0))
        self.assertEqual(target_completed.time_seconds, int(parsed.summary.get("duration_s") or 0))
        self.assertEqual(target_completed.avg_hr, parsed.summary.get("avg_hr"))
        self.assertEqual(target_completed.note, "")
        self.assertEqual(target_completed.feel, "")

        self.assertEqual(untouched_completed.distance_m, 4444)
        self.assertEqual(untouched_completed.time_seconds, 333)
        self.assertEqual(untouched_completed.note, "manual keep")
        self.assertEqual(untouched_completed.feel, "188")

    @patch("dashboard.views_home.timezone.localdate")
    def test_garmin_week_sync_rejects_future_week(self, mocked_localdate):
        mocked_localdate.return_value = date(2026, 3, 1)
        self._connect_garmin()

        resp = self.client.post(
            reverse("garmin_sync_week"),
            data={"week_start": "2026-03-02"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 400)
        payload = resp.json()
        self.assertFalse(payload["ok"])
        self.assertIn("az od zacatku tydne", payload["error"])

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
