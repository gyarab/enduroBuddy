from __future__ import annotations

from ._fit_import_base import (
    Activity,
    ActivityFile,
    ActivityImportLedger,
    BytesIO,
    CompletedTraining,
    FIXTURES_DIR,
    ImportJob,
    PlannedTraining,
    SimpleUploadedFile,
    TrainingMonth,
    TrainingWeek,
    _resolve_week_for_day,
    date,
    get_user_model,
    override_settings,
    parse_fit_file,
    reverse,
    timezone,
)


class DashboardFitImportFlowCases:
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
            data={"fit_file": SimpleUploadedFile(name=fit_path.name, content=fit_bytes, content_type="application/octet-stream")},
        )
        self.assertEqual(resp.status_code, 302)
        month = TrainingMonth.objects.get(athlete=self.user, year=run_day.year, month=run_day.month)
        week = TrainingWeek.objects.get(training_month=month, planned_trainings__date=run_day)
        planned = PlannedTraining.objects.get(week=week, date=run_day)
        activity = Activity.objects.get(planned_training=planned, athlete=self.user)
        completed = CompletedTraining.objects.get(planned=planned)
        self.assertEqual(completed.activity_id, activity.id)
        self.assertEqual(completed.distance_m, activity.distance_m)

    def test_import_training_skips_duplicate_file(self):
        fit_path = FIXTURES_DIR / "Z3.fit"
        fit_bytes = fit_path.read_bytes()
        payload = {"fit_file": SimpleUploadedFile(name=fit_path.name, content=fit_bytes, content_type="application/octet-stream")}
        self.assertEqual(self.client.post(reverse("dashboard_home"), data=payload).status_code, 302)
        payload2 = {"fit_file": SimpleUploadedFile(name=fit_path.name, content=fit_bytes, content_type="application/octet-stream")}
        self.assertEqual(self.client.post(reverse("dashboard_home"), data=payload2).status_code, 302)
        self.assertEqual(Activity.objects.filter(athlete=self.user).count(), 1)
        self.assertEqual(ActivityFile.objects.filter(activity__athlete=self.user).count(), 1)

    def test_custom_week_boundaries_follow_monday_start_rule(self):
        w_feb_23 = _resolve_week_for_day(self.user, timezone.datetime(2026, 2, 23).date())
        w_mar_1 = _resolve_week_for_day(self.user, timezone.datetime(2026, 3, 1).date())
        self.assertEqual((w_feb_23.training_month.month, w_feb_23.week_index), (2, 4))
        self.assertEqual((w_mar_1.training_month.month, w_mar_1.week_index), (2, 4))

    @override_settings(DEBUG=True)
    def test_dashboard_can_render_test_notifications_from_query_param(self):
        resp = self.client.get(reverse("dashboard_home"), {"test_notifications": "1"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Test: Nový tréninkový plán je připraven.")
        self.assertContains(resp, "Test: Garmin synchronizace bude spuštěna za chvíli.")

    @override_settings(DEBUG=True)
    def test_dashboard_can_render_full_test_notification_suite_from_query_param(self):
        resp = self.client.get(reverse("dashboard_home"), {"test_notifications": "all"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "ebTestClientNotifications")
        self.assertContains(resp, "Test client:")

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
        self.assertEqual(payload["job"]["progress_percent"], 50)

    @override_settings(DEBUG=True)
    def test_test_garmin_import_query_cleans_admin_week_and_completed(self):
        User = get_user_model()
        admin = User.objects.create_user(username="admin", password="admin")
        self.client.login(username="admin", password="admin")
        year = timezone.localdate().year
        run_day = date(year, 3, 4)
        week = _resolve_week_for_day(admin, run_day)
        planned = PlannedTraining.objects.create(week=week, date=run_day, day_label="Wed", title="Test run", order_in_day=1)
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
        self.assertFalse(Activity.objects.filter(id=activity.id).exists())

    @override_settings(DEBUG=True)
    def test_remove_week_completed_query_cleans_only_completed_for_selected_admin_week(self):
        User = get_user_model()
        admin = User.objects.create_user(username="admin", password="admin")
        self.client.login(username="admin", password="admin")
        week = _resolve_week_for_day(admin, date(2026, 3, 4))
        target = PlannedTraining.objects.create(week=week, date=date(2026, 3, 4), day_label="Wed", title="Target run", order_in_day=1)
        keep = PlannedTraining.objects.create(week=week, date=date(2026, 3, 5), day_label="Thu", title="Keep row", order_in_day=1)
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
        self.assertFalse(Activity.objects.filter(id=target_activity.id).exists())
        self.assertFalse(Activity.objects.filter(id=keep_activity.id).exists())
