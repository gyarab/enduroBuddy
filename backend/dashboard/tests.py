from __future__ import annotations

from io import BytesIO
from pathlib import Path
from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from dashboard.views import _resolve_week_for_day
from activities.models import Activity, ActivityFile, ActivityInterval
from activities.services.fit_parser import parse_fit_file
from training.models import CompletedTraining, PlannedTraining, TrainingMonth, TrainingWeek


FIXTURES_DIR = Path(__file__).resolve().parent.parent / "activities" / "tests" / "fixtures" / "fit"


class DashboardFitImportTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="runner", password="runner")
        self.client.login(username="runner", password="runner")

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
        # 23.2.2026-1.3.2026 is week 4 and last week of February
        w_feb_23 = _resolve_week_for_day(self.user, timezone.datetime(2026, 2, 23).date())
        w_mar_1 = _resolve_week_for_day(self.user, timezone.datetime(2026, 3, 1).date())
        self.assertEqual(w_feb_23.training_month.year, 2026)
        self.assertEqual(w_feb_23.training_month.month, 2)
        self.assertEqual(w_feb_23.week_index, 4)
        self.assertEqual(w_mar_1.training_month.year, 2026)
        self.assertEqual(w_mar_1.training_month.month, 2)
        self.assertEqual(w_mar_1.week_index, 4)

        # March starts with week 1 on 2.3.2026 and has 5 weeks, last starts 30.3.2026
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
        a1 = Activity.objects.create(
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
        a3 = Activity.objects.create(
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
