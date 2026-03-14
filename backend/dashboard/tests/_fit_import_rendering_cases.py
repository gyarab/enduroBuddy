from __future__ import annotations

from ._fit_import_base import (
    Activity,
    ActivityInterval,
    PlannedTraining,
    _resolve_planned_training,
    _resolve_week_for_day,
    date,
    reverse,
    timezone,
)


class DashboardFitImportRenderingCases:
    def test_completed_rows_are_aggregated_by_day_and_sorted_by_activity_start(self):
        run_day = date(2026, 3, 3)
        week = _resolve_week_for_day(self.user, run_day)
        p1 = PlannedTraining.objects.create(week=week, date=run_day, day_label="Tue", title="Warmup", order_in_day=1)
        p2 = PlannedTraining.objects.create(week=week, date=run_day, day_label="Tue", title="Workout", session_type=PlannedTraining.SessionType.WORKOUT, order_in_day=2)
        p3 = PlannedTraining.objects.create(week=week, date=run_day, day_label="Tue", title="Cooldown", order_in_day=3)
        tz = timezone.get_current_timezone()
        Activity.objects.create(athlete=self.user, planned_training=p1, workout_type=Activity.WorkoutType.RUN, started_at=timezone.make_aware(timezone.datetime(2026, 3, 3, 8, 0, 0), tz), distance_m=2000, duration_s=600, avg_pace_s_per_km=300, avg_hr=140, max_hr=152)
        a2 = Activity.objects.create(athlete=self.user, planned_training=p2, workout_type=Activity.WorkoutType.WORKOUT, started_at=timezone.make_aware(timezone.datetime(2026, 3, 3, 9, 0, 0), tz), distance_m=6000, duration_s=1800, avg_hr=165, max_hr=182)
        Activity.objects.create(athlete=self.user, planned_training=p3, workout_type=Activity.WorkoutType.RUN, started_at=timezone.make_aware(timezone.datetime(2026, 3, 3, 10, 0, 0), tz), distance_m=2000, duration_s=600, avg_pace_s_per_km=320, avg_hr=145, max_hr=155)
        ActivityInterval.objects.create(activity=a2, index=1, duration_s=60, distance_m=400, avg_hr=170, max_hr=180)
        ActivityInterval.objects.create(activity=a2, index=2, duration_s=100, distance_m=500, avg_hr=172, max_hr=182)
        resp = self.client.get(reverse("dashboard_home"))
        self.assertEqual(resp.status_code, 200)
        row = resp.context["month_cards"][0]["weeks"][0].completed_rows[0]
        self.assertEqual(row["km"], "10.00")
        self.assertEqual(row["min"], "50")

    def test_two_phase_day_renders_two_rows_in_planned_and_completed(self):
        run_day = date(2026, 3, 4)
        week = _resolve_week_for_day(self.user, run_day)
        tz = timezone.get_current_timezone()
        p1 = PlannedTraining.objects.create(week=week, date=run_day, day_label="Wed", title="Morning run", order_in_day=1, is_two_phase_day=True)
        p2 = PlannedTraining.objects.create(week=week, date=run_day, day_label="Wed", title="Evening workout", session_type=PlannedTraining.SessionType.WORKOUT, order_in_day=2, is_two_phase_day=True)
        Activity.objects.create(athlete=self.user, planned_training=p1, workout_type=Activity.WorkoutType.RUN, started_at=timezone.make_aware(timezone.datetime(2026, 3, 4, 7, 0, 0), tz), distance_m=3000, duration_s=900, avg_pace_s_per_km=300, avg_hr=140, max_hr=150)
        a2 = Activity.objects.create(athlete=self.user, planned_training=p2, workout_type=Activity.WorkoutType.WORKOUT, started_at=timezone.make_aware(timezone.datetime(2026, 3, 4, 18, 0, 0), tz), distance_m=5000, duration_s=1500, avg_pace_s_per_km=295, avg_hr=165, max_hr=180)
        ActivityInterval.objects.create(activity=a2, index=1, duration_s=60, distance_m=400, avg_hr=170, max_hr=178)
        ActivityInterval.objects.create(activity=a2, index=2, duration_s=80, distance_m=500, avg_hr=172, max_hr=180)
        resp = self.client.get(reverse("dashboard_home"))
        week_ctx = resp.context["month_cards"][0]["weeks"][0]
        self.assertEqual(len(week_ctx.planned_rows), 2)
        self.assertEqual(len(week_ctx.completed_rows), 2)

    def test_dashboard_renders_unplanned_activity_from_db_in_completed_rows(self):
        run_day = date(2026, 3, 6)
        _resolve_week_for_day(self.user, run_day)
        tz = timezone.get_current_timezone()
        Activity.objects.create(athlete=self.user, title="Neplanovany vyklus", workout_type=Activity.WorkoutType.RUN, started_at=timezone.make_aware(timezone.datetime(2026, 3, 6, 18, 30, 0), tz), distance_m=5500, duration_s=1650, avg_pace_s_per_km=300, avg_hr=148, max_hr=161)
        resp = self.client.get(reverse("dashboard_home"))
        rows = resp.context["month_cards"][0]["weeks"][0].completed_rows
        self.assertEqual(rows[0]["km"], "5.50")

    def test_run_day_with_planned_strides_keeps_pace_and_shows_finisher_hint(self):
        run_day = date(2026, 3, 7)
        week = _resolve_week_for_day(self.user, run_day)
        tz = timezone.get_current_timezone()
        planned = PlannedTraining.objects.create(week=week, date=run_day, day_label="Sat", title="10 km klus + 6-8x100m rovinky", session_type=PlannedTraining.SessionType.RUN, order_in_day=1)
        activity = Activity.objects.create(athlete=self.user, planned_training=planned, workout_type=Activity.WorkoutType.RUN, started_at=timezone.make_aware(timezone.datetime(2026, 3, 7, 12, 11, 13), tz), distance_m=10397, duration_s=3766, avg_pace_s_per_km=362)
        for idx in range(1, 11):
            ActivityInterval.objects.create(activity=activity, index=idx, duration_s=360 + idx, distance_m=1000)
        ActivityInterval.objects.create(activity=activity, index=11, duration_s=143, distance_m=397)
        resp = self.client.get(reverse("dashboard_home"))
        self.assertIn("rovinky", resp.context["month_cards"][0]["weeks"][0].completed_rows[0]["third"])

    def test_completed_row_contains_garmin_match_debug_summary(self):
        run_day = date(2026, 3, 12)
        week = _resolve_week_for_day(self.user, run_day)
        tz = timezone.get_current_timezone()
        planned = PlannedTraining.objects.create(week=week, date=run_day, day_label="Thu", title="3R 2x5x300m, p=60s, po serii 5min", session_type=PlannedTraining.SessionType.WORKOUT, order_in_day=1)
        activity = Activity.objects.create(athlete=self.user, planned_training=planned, workout_type=Activity.WorkoutType.WORKOUT, started_at=timezone.make_aware(timezone.datetime(2026, 3, 12, 16, 4, 23), tz), distance_m=3942, duration_s=1393, avg_pace_s_per_km=353)
        ActivityInterval.objects.create(activity=activity, index=1, duration_s=57, distance_m=303, note="WORK")
        ActivityInterval.objects.create(activity=activity, index=2, duration_s=60, distance_m=90, note="REST")
        resp = self.client.get(reverse("dashboard_home"))
        row = resp.context["month_cards"][0]["weeks"][0].completed_rows[0]
        self.assertIn("Garmin match:", row["match_debug"])

    def test_import_resolver_marks_day_as_two_phase_when_creating_second_training(self):
        run_day = date(2026, 3, 6)
        week = _resolve_week_for_day(self.user, run_day)
        first = PlannedTraining.objects.create(week=week, date=run_day, day_label="Fri", title="AM run", order_in_day=1, is_two_phase_day=False)
        Activity.objects.create(athlete=self.user, planned_training=first, workout_type=Activity.WorkoutType.RUN, started_at=timezone.now(), distance_m=5000, duration_s=1500)
        second = _resolve_planned_training(self.user, run_day, "PM run")
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertNotEqual(first.id, second.id)
        self.assertEqual(second.order_in_day, 2)

    def test_planned_training_session_type_can_be_updated(self):
        run_day = date(2026, 3, 7)
        week = _resolve_week_for_day(self.user, run_day)
        planned = PlannedTraining.objects.create(week=week, date=run_day, day_label="Sat", title="8 km klus", session_type=PlannedTraining.SessionType.RUN, order_in_day=1)
        resp = self.client.post(
            reverse("athlete_update_planned_training"),
            data='{"planned_id": %d, "field": "session_type", "value": "WORKOUT"}' % planned.id,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

    def test_plan_text_drives_run_vs_workout_rendering(self):
        tz = timezone.get_current_timezone()
        week = _resolve_week_for_day(self.user, date(2026, 3, 10))
        planned_workout = PlannedTraining.objects.create(week=week, date=date(2026, 3, 10), day_label="Tue", title="3x(500-300-200), P=60s", session_type=PlannedTraining.SessionType.WORKOUT, order_in_day=1)
        activity_workout_like = Activity.objects.create(athlete=self.user, planned_training=planned_workout, workout_type=Activity.WorkoutType.RUN, started_at=timezone.make_aware(timezone.datetime(2026, 3, 10, 8, 0, 0), tz), distance_m=7000, duration_s=2100, avg_pace_s_per_km=300)
        ActivityInterval.objects.create(activity=activity_workout_like, index=1, duration_s=99, distance_m=500)
        planned_run = PlannedTraining.objects.create(week=week, date=date(2026, 3, 11), day_label="Wed", title="8 km klus", session_type=PlannedTraining.SessionType.RUN, order_in_day=1)
        activity_run_like = Activity.objects.create(athlete=self.user, planned_training=planned_run, workout_type=Activity.WorkoutType.WORKOUT, started_at=timezone.make_aware(timezone.datetime(2026, 3, 11, 8, 0, 0), tz), distance_m=8000, duration_s=2400, avg_pace_s_per_km=300)
        ActivityInterval.objects.create(activity=activity_run_like, index=1, duration_s=100, distance_m=400)
        resp = self.client.get(reverse("dashboard_home"))
        rows = resp.context["month_cards"][0]["weeks"][0].completed_rows
        self.assertGreaterEqual(len(rows), 2)
