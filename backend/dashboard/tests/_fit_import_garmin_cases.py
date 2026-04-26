from __future__ import annotations

from django.test import override_settings

from ._fit_import_base import (
    Activity,
    CompletedTraining,
    FIXTURES_DIR,
    GarminConnection,
    GarminDownloadResult,
    GarminFitPayload,
    PlannedTraining,
    BytesIO,
    _resolve_week_for_day,
    _select_payloads_for_import,
    date,
    parse_fit_file,
    patch,
    reverse,
    timedelta,
    timezone,
)


class DashboardFitImportGarminCases:
    @patch("dashboard.services.imports._parse_payload_metadata_for_user")
    def test_select_payloads_prefers_interval_rich_workout_when_plan_expects_workout(self, mocked_metadata):
        run_day = date(2026, 3, 12)
        week = _resolve_week_for_day(self.user, run_day)
        PlannedTraining.objects.create(week=week, date=run_day, day_label="Thu", title="3R 2x5x300m, p=60s, po serii 5min", session_type=PlannedTraining.SessionType.WORKOUT, order_in_day=1)
        payloads = [
            GarminFitPayload(activity_id="22163202434", original_name="garmin_22163202434.fit", fit_bytes=b"a"),
            GarminFitPayload(activity_id="22163202422", original_name="garmin_22163202422.fit", fit_bytes=b"b"),
            GarminFitPayload(activity_id="22163202419", original_name="garmin_22163202419.fit", fit_bytes=b"c"),
        ]
        mocked_metadata.side_effect = lambda *, fit_bytes: {
            b"a": {"run_day": run_day, "workout_type": Activity.WorkoutType.WORKOUT, "distance_m": 4492, "duration_s": 1249, "interval_count": 5, "work_interval_count": 5, "rest_interval_count": 0},
            b"b": {"run_day": run_day, "workout_type": Activity.WorkoutType.WORKOUT, "distance_m": 3942, "duration_s": 1393, "interval_count": 20, "work_interval_count": 10, "rest_interval_count": 10},
            b"c": {"run_day": run_day, "workout_type": Activity.WorkoutType.RUN, "distance_m": 3038, "duration_s": 893, "interval_count": 4, "work_interval_count": 0, "rest_interval_count": 0},
        }[fit_bytes]
        selected = _select_payloads_for_import(user=self.user, payloads=payloads)
        self.assertEqual([payload.activity_id for payload in selected], ["22163202422"])

    @patch("dashboard.services.imports._parse_payload_metadata_for_user")
    def test_select_payloads_matches_two_phase_day_by_planned_session_type(self, mocked_metadata):
        run_day = date(2026, 3, 12)
        week = _resolve_week_for_day(self.user, run_day)
        PlannedTraining.objects.create(week=week, date=run_day, day_label="Thu", title="3 km vyklus", session_type=PlannedTraining.SessionType.RUN, order_in_day=1, is_two_phase_day=True)
        PlannedTraining.objects.create(week=week, date=run_day, day_label="Thu", title="3R 2x5x300m, p=60s, po serii 5min", session_type=PlannedTraining.SessionType.WORKOUT, order_in_day=2, is_two_phase_day=True)
        payloads = [
            GarminFitPayload(activity_id="22163202419", original_name="garmin_22163202419.fit", fit_bytes=b"run"),
            GarminFitPayload(activity_id="22163202422", original_name="garmin_22163202422.fit", fit_bytes=b"workout"),
            GarminFitPayload(activity_id="22163202434", original_name="garmin_22163202434.fit", fit_bytes=b"other"),
        ]
        mocked_metadata.side_effect = lambda *, fit_bytes: {
            b"run": {"run_day": run_day, "workout_type": Activity.WorkoutType.RUN, "distance_m": 3038, "duration_s": 893, "interval_count": 4, "work_interval_count": 0, "rest_interval_count": 0},
            b"workout": {"run_day": run_day, "workout_type": Activity.WorkoutType.WORKOUT, "distance_m": 3942, "duration_s": 1393, "interval_count": 20, "work_interval_count": 10, "rest_interval_count": 10},
            b"other": {"run_day": run_day, "workout_type": Activity.WorkoutType.WORKOUT, "distance_m": 4492, "duration_s": 1249, "interval_count": 5, "work_interval_count": 5, "rest_interval_count": 0},
        }[fit_bytes]
        selected = _select_payloads_for_import(user=self.user, payloads=payloads)
        self.assertEqual([payload.activity_id for payload in selected], ["22163202419", "22163202422"])

    @patch("dashboard.services.imports._parse_payload_metadata_for_user")
    def test_select_payloads_logs_match_reason_for_single_day(self, mocked_metadata):
        run_day = date(2026, 3, 12)
        week = _resolve_week_for_day(self.user, run_day)
        PlannedTraining.objects.create(week=week, date=run_day, day_label="Thu", title="3R 2x5x300m, p=60s, po serii 5min", session_type=PlannedTraining.SessionType.WORKOUT, order_in_day=1)
        payloads = [
            GarminFitPayload(activity_id="22163202434", original_name="garmin_22163202434.fit", fit_bytes=b"a"),
            GarminFitPayload(activity_id="22163202422", original_name="garmin_22163202422.fit", fit_bytes=b"b"),
        ]
        mocked_metadata.side_effect = lambda *, fit_bytes: {
            b"a": {"run_day": run_day, "workout_type": Activity.WorkoutType.WORKOUT, "distance_m": 4492, "duration_s": 1249, "interval_count": 5, "work_interval_count": 5, "rest_interval_count": 0},
            b"b": {"run_day": run_day, "workout_type": Activity.WorkoutType.WORKOUT, "distance_m": 3942, "duration_s": 1393, "interval_count": 20, "work_interval_count": 10, "rest_interval_count": 10},
        }[fit_bytes]
        with self.assertLogs("dashboard.services.imports", level="DEBUG") as cm:
            selected = _select_payloads_for_import(user=self.user, payloads=payloads)
        self.assertEqual([payload.activity_id for payload in selected], ["22163202422"])
        self.assertTrue(any("Garmin match day=2026-03-12 mode=single" in line for line in cm.output))

    @patch("dashboard.services.imports.download_garmin_fit_payloads")
    def test_garmin_week_sync_replaces_only_days_with_new_payloads(self, mocked_download):
        fit_path = FIXTURES_DIR / "Z3.fit"
        fit_bytes = fit_path.read_bytes()
        parsed = parse_fit_file(BytesIO(fit_bytes))
        started_at = parsed.summary.get("started_at")
        if timezone.is_naive(started_at):
            started_at = timezone.make_aware(started_at, timezone.get_current_timezone())
        run_day = timezone.localtime(started_at).date()
        week = _resolve_week_for_day(self.user, run_day)
        other_day = run_day + timedelta(days=1)
        target = PlannedTraining.objects.create(week=week, date=run_day, day_label="Run", title="Target", order_in_day=1)
        untouched = PlannedTraining.objects.create(week=week, date=other_day, day_label="Keep", title="Keep", order_in_day=1)
        CompletedTraining.objects.create(planned=target, time_seconds=111, distance_m=2222, avg_hr=123, note="manual target", feel="199")
        CompletedTraining.objects.create(planned=untouched, time_seconds=333, distance_m=4444, avg_hr=145, note="manual keep", feel="188")
        self._connect_garmin()
        mocked_download.return_value = GarminDownloadResult(payloads=[GarminFitPayload(activity_id="1001", original_name="garmin_1001.fit", fit_bytes=fit_bytes)], refreshed_tokenstore="new-token")
        week_start = run_day - timedelta(days=run_day.weekday())
        resp = self.client.post(reverse("garmin_sync_week"), data={"week_start": week_start.isoformat()}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["replaced_count"], 1)

    @patch("dashboard.views_home.timezone.localdate")
    def test_garmin_week_sync_rejects_future_week(self, mocked_localdate):
        mocked_localdate.return_value = date(2026, 3, 1)
        self._connect_garmin()
        resp = self.client.post(reverse("garmin_sync_week"), data={"week_start": "2026-03-02"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(resp.status_code, 400)

    @override_settings(GARMIN_SYNC_ENABLED=False)
    def test_garmin_week_sync_endpoint_can_be_disabled_via_settings(self):
        self._connect_garmin()
        resp = self.client.post(reverse("garmin_sync_week"), data={"week_start": "2026-03-02"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(resp.status_code, 503)
