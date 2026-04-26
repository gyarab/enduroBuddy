from __future__ import annotations

from ._fit_import_base import (
    ImportJob,
    PlannedTraining,
    TrainingMonth,
    TrainingWeek,
    _resolve_week_for_day,
    date,
    get_user_model,
    override_settings,
    reverse,
    timezone,
)


class DashboardFitImportFlowCases:
    def test_custom_week_boundaries_follow_monday_start_rule(self):
        w_feb_23 = _resolve_week_for_day(self.user, timezone.datetime(2026, 2, 23).date())
        w_mar_1 = _resolve_week_for_day(self.user, timezone.datetime(2026, 3, 1).date())
        self.assertEqual((w_feb_23.training_month.month, w_feb_23.week_index), (2, 4))
        self.assertEqual((w_mar_1.training_month.month, w_mar_1.week_index), (2, 4))

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
