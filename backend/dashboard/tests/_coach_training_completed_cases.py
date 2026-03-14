from __future__ import annotations

from ._coach_training_base import Activity, CompletedTraining, PlannedTraining, _resolve_week_for_day, date, json, patch, reverse


class CoachTrainingCompletedCases:
    def test_coach_page_renders_empty_completed_training_as_editable(self):
        planned = PlannedTraining.objects.filter(week__training_month__athlete=self.athlete).first()
        self.assertIsNotNone(planned)
        self.client.login(username="coach", password="coach")
        resp = self.client.get(reverse("coach_training_plans"), {"athlete": self.athlete.id})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context["completed_editable"])
        self.assertEqual(resp.context["completed_update_url"], "")

    def test_coach_cannot_inline_update_completed_training_for_athlete_even_when_empty(self):
        planned = PlannedTraining.objects.filter(week__training_month__athlete=self.athlete).first()
        self.assertIsNotNone(planned)
        self.client.login(username="coach", password="coach")
        resp = self.client.post(
            reverse("coach_update_completed_training"),
            data=json.dumps({"planned_id": planned.id, "field": "km", "value": "8.50"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(CompletedTraining.objects.filter(planned=planned).exists())

    def test_coach_cannot_inline_update_completed_training_with_linked_activity(self):
        planned = PlannedTraining.objects.filter(week__training_month__athlete=self.athlete).first()
        self.assertIsNotNone(planned)
        activity = Activity.objects.create(athlete=self.athlete, planned_training=planned, distance_m=5000, duration_s=1500)
        CompletedTraining.objects.create(planned=planned, activity=activity, distance_m=5000, time_seconds=1500)
        self.client.login(username="coach", password="coach")
        resp = self.client.post(
            reverse("coach_update_completed_training"),
            data=json.dumps({"planned_id": planned.id, "field": "km", "value": "8.50"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_coach_page_renders_linked_completed_training_as_read_only(self):
        planned = PlannedTraining.objects.filter(week__training_month__athlete=self.athlete).first()
        self.assertIsNotNone(planned)
        activity = Activity.objects.create(athlete=self.athlete, distance_m=5000, duration_s=1500)
        CompletedTraining.objects.create(planned=planned, activity=activity, distance_m=5000, time_seconds=1500)
        self.client.login(username="coach", password="coach")
        resp = self.client.get(reverse("coach_training_plans"), {"athlete": self.athlete.id})
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, f'contenteditable="true" data-training-id="{planned.id}" data-field="km"')

    def test_coach_can_inline_update_completed_training_for_own_plan(self):
        own_week = _resolve_week_for_day(self.coach, date(2026, 3, 6))
        own_planned = PlannedTraining.objects.create(week=own_week, date=date(2026, 3, 6), day_label="Fri", title="Own easy run", order_in_day=1)
        self.client.login(username="coach", password="coach")
        own_page = self.client.get(reverse("coach_training_plans"), {"athlete": self.coach.id})
        self.assertEqual(own_page.status_code, 200)
        self.assertTrue(own_page.context["completed_editable"])
        resp = self.client.post(
            reverse("coach_update_completed_training"),
            data=json.dumps({"planned_id": own_planned.id, "field": "km", "value": "7.00"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        completed = CompletedTraining.objects.get(planned=own_planned)
        self.assertEqual(completed.distance_m, 7000)

    def test_athlete_can_inline_update_own_completed_training(self):
        planned = PlannedTraining.objects.filter(week__training_month__athlete=self.athlete).first()
        self.assertIsNotNone(planned)
        self.client.login(username="athlete", password="athlete")
        resp = self.client.post(
            reverse("athlete_update_completed_training"),
            data=json.dumps({"planned_id": planned.id, "field": "third", "value": "easy + strides"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        completed = CompletedTraining.objects.get(planned=planned)
        self.assertEqual(completed.note, "easy + strides")

    def test_completed_update_noop_value_skips_save(self):
        planned = PlannedTraining.objects.filter(week__training_month__athlete=self.athlete).first()
        self.assertIsNotNone(planned)
        self.client.login(username="athlete", password="athlete")
        first = self.client.post(
            reverse("athlete_update_completed_training"),
            data=json.dumps({"planned_id": planned.id, "field": "km", "value": "8.50"}),
            content_type="application/json",
        )
        self.assertEqual(first.status_code, 200)
        with patch("dashboard.views.CompletedTraining.save") as save_mock:
            second = self.client.post(
                reverse("athlete_update_completed_training"),
                data=json.dumps({"planned_id": planned.id, "field": "km", "value": "8.50"}),
                content_type="application/json",
            )
        self.assertEqual(second.status_code, 200)
        save_mock.assert_not_called()

    def test_clearing_last_manual_completed_value_deletes_completed_row(self):
        planned = PlannedTraining.objects.filter(week__training_month__athlete=self.athlete).first()
        self.assertIsNotNone(planned)
        CompletedTraining.objects.create(planned=planned, note="easy + strides")
        self.client.login(username="athlete", password="athlete")

        resp = self.client.post(
            reverse("athlete_update_completed_training"),
            data=json.dumps({"planned_id": planned.id, "field": "third", "value": ""}),
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(CompletedTraining.objects.filter(planned=planned).exists())

    def test_clearing_empty_linked_completed_value_deletes_completed_and_activity(self):
        planned = PlannedTraining.objects.filter(week__training_month__athlete=self.athlete).first()
        self.assertIsNotNone(planned)
        activity = Activity.objects.create(athlete=self.athlete, planned_training=planned, distance_m=5000, duration_s=1500)
        CompletedTraining.objects.create(planned=planned, activity=activity)
        self.client.login(username="athlete", password="athlete")

        resp = self.client.post(
            reverse("athlete_update_completed_training"),
            data=json.dumps({"planned_id": planned.id, "field": "third", "value": ""}),
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(CompletedTraining.objects.filter(planned=planned).exists())
        self.assertFalse(Activity.objects.filter(id=activity.id).exists())
