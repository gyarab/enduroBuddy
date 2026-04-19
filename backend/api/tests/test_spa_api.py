from __future__ import annotations

import json
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import AppNotification, CoachAthlete, GarminConnection, GarminSyncAudit, ImportJob, Role
from training.models import CompletedTraining, PlannedTraining, TrainingMonth, TrainingWeek


class SpaApiEndpointTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.athlete = User.objects.create_user(
            username="api-athlete",
            email="athlete@example.com",
            password="athlete-pass-123",
            first_name="Ava",
            last_name="Runner",
        )
        self.coach = User.objects.create_user(
            username="api-coach",
            email="coach@example.com",
            password="coach-pass-123",
            first_name="Coach",
            last_name="One",
        )
        self.coach.profile.role = Role.COACH
        self.coach.profile.save(update_fields=["role"])
        self.link = CoachAthlete.objects.create(
            coach=self.coach,
            athlete=self.athlete,
            focus="Z2",
            sort_order=1,
        )
        self.month = TrainingMonth.objects.create(athlete=self.athlete, year=2026, month=4)
        self.week = TrainingWeek.objects.create(training_month=self.month, week_index=1)
        self.planned = PlannedTraining.objects.create(
            week=self.week,
            date=date(2026, 4, 6),
            day_label="PO",
            title="Easy 8 km",
            notes="Keep it light",
            session_type=PlannedTraining.SessionType.RUN,
            planned_distance_km="8.00",
            order_in_day=1,
        )

    def test_auth_me_returns_role_capabilities_and_default_route(self):
        self.client.force_login(self.coach)

        response = self.client.get(reverse("api_auth_me"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["email"], "coach@example.com")
        self.assertEqual(payload["role"], Role.COACH)
        self.assertEqual(payload["default_app_route"], "/coach/plans")
        self.assertTrue(payload["capabilities"]["can_view_coach"])
        self.assertEqual(payload["capabilities"]["coached_athlete_count"], 1)

    def test_dashboard_returns_selected_month_summary_and_rows(self):
        self.client.force_login(self.athlete)

        response = self.client.get(reverse("api_dashboard"), {"month": "2026-04"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["selected_month"]["value"], "2026-04")
        self.assertEqual(payload["summary"]["planned_sessions"], 1)
        self.assertEqual(len(payload["weeks"]), 1)
        planned_row = payload["weeks"][0]["planned_rows"][0]
        self.assertEqual(planned_row["id"], self.planned.id)
        self.assertEqual(planned_row["title"], "Easy 8 km")
        self.assertTrue(planned_row["editable"])
        self.assertTrue(payload["flags"]["can_edit_completed"])

    def test_coach_dashboard_returns_selected_athlete_and_read_only_completed_flag(self):
        self.client.force_login(self.coach)

        response = self.client.get(
            reverse("api_coach_dashboard"),
            {"athlete_id": str(self.athlete.id), "month": "2026-04"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["selected_athlete"]["id"], self.athlete.id)
        self.assertEqual(payload["selected_athlete"]["focus"], "Z2")
        self.assertEqual(payload["athletes"][0]["id"], self.athlete.id)
        self.assertTrue(payload["flags"]["is_coach"])
        self.assertTrue(payload["flags"]["can_edit_planned"])
        self.assertFalse(payload["flags"]["can_edit_completed"])
        self.assertFalse(payload["weeks"][0]["completed_rows"][0]["editable"])

    def test_profile_completion_patch_updates_name_role_and_flags(self):
        self.client.force_login(self.athlete)

        response = self.patch_json(
            reverse("api_profile_complete"),
            {
                "first_name": "New",
                "last_name": "Coach",
                "role": Role.COACH,
                "next": "/coach/plans",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["redirect_to"], "/coach/plans")
        self.athlete.refresh_from_db()
        self.assertEqual(self.athlete.first_name, "New")
        self.assertEqual(self.athlete.last_name, "Coach")
        self.assertEqual(self.athlete.profile.role, Role.COACH)
        self.assertTrue(self.athlete.profile.google_profile_completed)
        self.assertTrue(self.athlete.profile.google_role_confirmed)

    def test_profile_settings_get_and_patch_return_spa_friendly_profile_surface(self):
        self.client.force_login(self.athlete)

        get_response = self.client.get(reverse("api_profile_settings"))
        patch_response = self.patch_json(
            reverse("api_profile_settings"),
            {
                "first_name": "Nova",
                "last_name": "Runner",
            },
        )

        self.assertEqual(get_response.status_code, 200)
        get_payload = get_response.json()
        self.assertTrue(get_payload["ok"])
        self.assertEqual(get_payload["profile"]["email"], "athlete@example.com")
        self.assertEqual(get_payload["profile"]["default_app_route"], "/app/dashboard")
        self.assertEqual(get_payload["profile"]["password_change_url"], "/accounts/password/change/")

        self.assertEqual(patch_response.status_code, 200)
        patch_payload = patch_response.json()
        self.assertTrue(patch_payload["ok"])
        self.assertEqual(patch_payload["profile"]["first_name"], "Nova")
        self.assertEqual(patch_payload["profile"]["last_name"], "Runner")
        self.athlete.refresh_from_db()
        self.assertEqual(self.athlete.first_name, "Nova")
        self.assertEqual(self.athlete.last_name, "Runner")

    def test_spa_routes_render_spa_template_for_authenticated_app_runtime(self):
        self.client.force_login(self.athlete)

        athlete_response = self.client.get("/app/dashboard")
        coach_response = self.client.get("/coach/plans")

        self.assertEqual(athlete_response.status_code, 200)
        self.assertEqual(coach_response.status_code, 200)
        self.assertTemplateUsed(athlete_response, "spa.html")
        self.assertTemplateUsed(coach_response, "spa.html")
        self.assertContains(athlete_response, 'id="app"')
        self.assertContains(coach_response, 'id="app"')

    def test_athlete_can_patch_own_planned_and_completed_training(self):
        self.client.force_login(self.athlete)

        planned_response = self.patch_json(
            reverse("api_training_planned_update", kwargs={"planned_id": self.planned.id}),
            {"field": "title", "value": "Tempo 6x400m"},
        )
        completed_response = self.patch_json(
            reverse("api_training_completed_update", kwargs={"planned_id": self.planned.id}),
            {"field": "km", "value": "6.4"},
        )

        self.assertEqual(planned_response.status_code, 200)
        self.assertEqual(completed_response.status_code, 200)
        self.planned.refresh_from_db()
        self.assertEqual(self.planned.title, "Tempo 6x400m")
        completed = CompletedTraining.objects.get(planned=self.planned)
        self.assertEqual(completed.distance_m, 6400)

    def test_athlete_can_create_and_delete_empty_planned_training(self):
        self.client.force_login(self.athlete)

        create_response = self.post_json(
            reverse("api_training_planned_create"),
            {
                "date": "2026-04-08",
                "title": "New easy run",
                "notes": "Keep it relaxed",
                "session_type": PlannedTraining.SessionType.RUN,
            },
        )

        self.assertEqual(create_response.status_code, 201)
        planned_id = create_response.json()["planned"]["id"]
        planned = PlannedTraining.objects.get(id=planned_id)
        self.assertEqual(planned.week.training_month.athlete, self.athlete)
        self.assertEqual(planned.title, "New easy run")
        self.assertEqual(planned.day_label, "St")

        delete_response = self.client.delete(reverse("api_training_planned_update", kwargs={"planned_id": planned_id}))

        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(PlannedTraining.objects.filter(id=planned_id).exists())

    def test_athlete_cannot_delete_planned_training_with_completed_data(self):
        CompletedTraining.objects.create(planned=self.planned, note="done")
        self.client.force_login(self.athlete)

        response = self.client.delete(reverse("api_training_planned_update", kwargs={"planned_id": self.planned.id}))

        self.assertEqual(response.status_code, 400)
        self.assertTrue(PlannedTraining.objects.filter(id=self.planned.id).exists())
        self.assertTrue(CompletedTraining.objects.filter(planned=self.planned).exists())

    def test_coach_can_patch_accessible_athlete_planned_training(self):
        self.client.force_login(self.coach)

        response = self.patch_json(
            reverse("api_coach_training_planned_update", kwargs={"planned_id": self.planned.id}),
            {"field": "notes", "value": "Coach adjusted note"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["field"], "notes")
        self.planned.refresh_from_db()
        self.assertEqual(self.planned.notes, "Coach adjusted note")

    def test_coach_can_create_and_delete_accessible_athlete_planned_training(self):
        self.client.force_login(self.coach)

        create_response = self.post_json(
            reverse("api_coach_training_planned_create"),
            {
                "athlete_id": self.athlete.id,
                "date": "2026-04-09",
                "title": "Coach created tempo",
                "session_type": PlannedTraining.SessionType.WORKOUT,
            },
        )

        self.assertEqual(create_response.status_code, 201)
        planned_id = create_response.json()["planned"]["id"]
        planned = PlannedTraining.objects.get(id=planned_id)
        self.assertEqual(planned.week.training_month.athlete, self.athlete)
        self.assertEqual(planned.session_type, PlannedTraining.SessionType.WORKOUT)

        delete_response = self.client.delete(reverse("api_coach_training_planned_update", kwargs={"planned_id": planned_id}))

        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(PlannedTraining.objects.filter(id=planned_id).exists())

    def test_coach_cannot_patch_managed_athlete_completed_training(self):
        self.client.force_login(self.coach)

        response = self.patch_json(
            reverse("api_coach_training_completed_update", kwargs={"planned_id": self.planned.id}),
            {"field": "km", "value": "7.0"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(CompletedTraining.objects.filter(planned=self.planned).exists())

    def test_coach_can_patch_own_completed_training(self):
        own_month = TrainingMonth.objects.create(athlete=self.coach, year=2026, month=4)
        own_week = TrainingWeek.objects.create(training_month=own_month, week_index=1)
        own_planned = PlannedTraining.objects.create(
            week=own_week,
            date=date(2026, 4, 7),
            day_label="UT",
            title="Coach easy run",
            order_in_day=1,
        )
        self.client.force_login(self.coach)

        response = self.patch_json(
            reverse("api_coach_training_completed_update", kwargs={"planned_id": own_planned.id}),
            {"field": "km", "value": "7.0"},
        )

        self.assertEqual(response.status_code, 200)
        completed = CompletedTraining.objects.get(planned=own_planned)
        self.assertEqual(completed.distance_m, 7000)

    def test_athlete_can_create_and_remove_second_phase(self):
        self.client.force_login(self.athlete)
        second_phase_url = reverse(
            "api_training_planned_second_phase",
            kwargs={"planned_id": self.planned.id},
        )

        create_response = self.client.post(second_phase_url)

        self.assertEqual(create_response.status_code, 200)
        created_id = create_response.json()["second_phase_planned_id"]
        self.assertTrue(PlannedTraining.objects.filter(id=created_id, is_two_phase_day=True).exists())
        self.planned.refresh_from_db()
        self.assertTrue(self.planned.is_two_phase_day)

        remove_response = self.client.delete(second_phase_url)

        self.assertEqual(remove_response.status_code, 200)
        self.assertFalse(PlannedTraining.objects.filter(id=created_id).exists())
        self.planned.refresh_from_db()
        self.assertFalse(self.planned.is_two_phase_day)

    def test_coach_manage_reorders_and_hides_athletes(self):
        User = get_user_model()
        second_athlete = User.objects.create_user(
            username="api-athlete-two",
            email="athlete-two@example.com",
            password="athlete-pass-123",
        )
        second_link = CoachAthlete.objects.create(
            coach=self.coach,
            athlete=second_athlete,
            focus="LT",
            sort_order=2,
        )
        self.client.force_login(self.coach)

        reorder_response = self.patch_json(
            reverse("api_coach_reorder_athletes"),
            {"athlete_ids": [second_athlete.id, self.athlete.id]},
        )
        visibility_response = self.patch_json(
            reverse("api_coach_athlete_visibility"),
            {"athlete_id": self.athlete.id, "hidden": True},
        )

        self.assertEqual(reorder_response.status_code, 200)
        self.link.refresh_from_db()
        second_link.refresh_from_db()
        self.assertEqual(second_link.sort_order, 1)
        self.assertEqual(self.link.sort_order, 2)
        self.assertEqual(visibility_response.status_code, 200)
        self.link.refresh_from_db()
        self.assertTrue(self.link.hidden_from_plans)

    def test_notifications_list_and_mark_read_are_scoped_to_current_user(self):
        notification = AppNotification.objects.create(
            recipient=self.athlete,
            actor=self.coach,
            kind=AppNotification.Kind.PLAN_UPDATED,
            tone=AppNotification.Tone.INFO,
            text="Plan updated",
        )
        AppNotification.objects.create(
            recipient=self.coach,
            actor=self.athlete,
            kind=AppNotification.Kind.COACH_NOTE,
            tone=AppNotification.Tone.INFO,
            text="Coach-only notification",
        )
        self.client.force_login(self.athlete)

        list_response = self.client.get(reverse("api_notifications"))
        mark_response = self.post_json(
            reverse("api_notifications_mark_read"),
            {"notification_ids": [notification.id]},
        )

        self.assertEqual(list_response.status_code, 200)
        list_payload = list_response.json()
        self.assertEqual(list_payload["unread_count"], 1)
        self.assertEqual(len(list_payload["notifications"]), 1)
        self.assertEqual(list_payload["notifications"][0]["id"], notification.id)
        self.assertEqual(mark_response.status_code, 200)
        self.assertEqual(mark_response.json()["marked_count"], 1)
        notification.refresh_from_db()
        self.assertIsNotNone(notification.read_at)

    def test_import_job_status_is_scoped_to_current_user(self):
        other_job = ImportJob.objects.create(
            user=self.coach,
            kind=ImportJob.Kind.GARMIN_SYNC,
            status=ImportJob.Status.QUEUED,
            window="last_7_days",
        )
        own_job = ImportJob.objects.create(
            user=self.athlete,
            kind=ImportJob.Kind.GARMIN_SYNC,
            status=ImportJob.Status.SUCCESS,
            window="last_30_days",
            total_count=2,
            processed_count=2,
            imported_count=1,
        )
        self.client.force_login(self.athlete)

        own_response = self.client.get(reverse("api_imports_job_status", kwargs={"job_id": own_job.id}))
        other_response = self.client.get(reverse("api_imports_job_status", kwargs={"job_id": other_job.id}))
        missing_file_response = self.client.post(reverse("api_imports_fit"))

        self.assertEqual(own_response.status_code, 200)
        self.assertEqual(own_response.json()["job"]["id"], own_job.id)
        self.assertEqual(other_response.status_code, 404)
        self.assertEqual(missing_file_response.status_code, 400)

    @override_settings(GARMIN_SYNC_ENABLED=True)
    @patch("api.views.imports.enqueue_garmin_sync_job")
    def test_garmin_sync_start_creates_job_and_reuses_active_job(self, enqueue_mock):
        GarminConnection.objects.create(
            user=self.athlete,
            garmin_email="runner@example.com",
            garmin_display_name="Runner",
            encrypted_tokenstore="encrypted-tokenstore",
            is_active=True,
        )
        self.client.force_login(self.athlete)

        first_response = self.post_json(reverse("api_imports_garmin_start"), {"range": "this_week"})
        second_response = self.post_json(reverse("api_imports_garmin_start"), {"range": "yesterday"})

        self.assertEqual(first_response.status_code, 200)
        first_payload = first_response.json()
        self.assertTrue(first_payload["ok"])
        self.assertFalse(first_payload["already_running"])
        job = ImportJob.objects.get(id=first_payload["job"]["id"])
        self.assertEqual(job.user, self.athlete)
        self.assertEqual(job.window, "this_week")
        self.assertEqual(job.status, ImportJob.Status.QUEUED)
        enqueue_mock.assert_called_once_with(job.id)

        self.assertEqual(second_response.status_code, 200)
        second_payload = second_response.json()
        self.assertTrue(second_payload["already_running"])
        self.assertEqual(second_payload["job"]["id"], job.id)
        self.assertEqual(ImportJob.objects.filter(user=self.athlete, kind=ImportJob.Kind.GARMIN_SYNC).count(), 1)

    def test_garmin_revoke_deactivates_connection_and_writes_audit(self):
        connection = GarminConnection.objects.create(
            user=self.athlete,
            garmin_email="runner@example.com",
            garmin_display_name="Runner",
            encrypted_tokenstore="encrypted-tokenstore",
            is_active=True,
        )
        self.client.force_login(self.athlete)

        response = self.client.post(reverse("api_imports_garmin_revoke"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["connection"]["connected"])
        connection.refresh_from_db()
        self.assertFalse(connection.is_active)
        self.assertEqual(connection.encrypted_tokenstore, "")
        self.assertIsNotNone(connection.revoked_at)
        self.assertTrue(
            GarminSyncAudit.objects.filter(
                user=self.athlete,
                action=GarminSyncAudit.Action.REVOKE,
                status=GarminSyncAudit.Status.SUCCESS,
            ).exists()
        )

    def patch_json(self, url: str, payload: dict):
        return self.client.patch(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )

    def post_json(self, url: str, payload: dict):
        return self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )
