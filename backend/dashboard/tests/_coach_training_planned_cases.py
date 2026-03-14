from __future__ import annotations

from ._coach_training_base import CoachAthlete, PlannedTraining, _resolve_week_for_day, date, json, patch, reverse


class CoachTrainingPlannedCases:
    def test_coach_can_inline_update_planned_training_title_and_notes(self):
        planned = PlannedTraining.objects.filter(week__training_month__athlete=self.athlete).first()
        self.assertIsNotNone(planned)
        self.client.login(username="coach", password="coach")
        resp_title = self.client.post(
            reverse("coach_update_planned_training"),
            data=json.dumps({"planned_id": planned.id, "field": "title", "value": "Intervals 8x400"}),
            content_type="application/json",
        )
        self.assertEqual(resp_title.status_code, 200)
        planned.refresh_from_db()
        self.assertEqual(planned.title, "Intervals 8x400")
        resp_notes = self.client.post(
            reverse("coach_update_planned_training"),
            data=json.dumps({"planned_id": planned.id, "field": "notes", "value": "Keep HR under threshold."}),
            content_type="application/json",
        )
        self.assertEqual(resp_notes.status_code, 200)
        planned.refresh_from_db()
        self.assertEqual(planned.notes, "Keep HR under threshold.")

    def test_inline_title_update_stores_planned_distance_from_title(self):
        planned = PlannedTraining.objects.filter(week__training_month__athlete=self.athlete).first()
        self.assertIsNotNone(planned)
        self.client.login(username="coach", password="coach")
        resp = self.client.post(
            reverse("coach_update_planned_training"),
            data=json.dumps({"planned_id": planned.id, "field": "title", "value": "Easy run 11,7 km"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        planned.refresh_from_db()
        self.assertEqual(str(planned.planned_distance_km), "11.70")

    def test_coach_can_inline_update_own_planned_training(self):
        own_week = _resolve_week_for_day(self.coach, date(2026, 3, 8))
        own_planned = PlannedTraining.objects.create(
            week=own_week, date=date(2026, 3, 8), day_label="Sun", title="Coach base run", notes="", order_in_day=1
        )
        self.client.login(username="coach", password="coach")
        resp = self.client.post(
            reverse("coach_update_planned_training"),
            data=json.dumps({"planned_id": own_planned.id, "field": "title", "value": "Coach updated"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        own_planned.refresh_from_db()
        self.assertEqual(own_planned.title, "Coach updated")

    def test_other_coach_cannot_inline_update_foreign_athlete_planned_training(self):
        week = _resolve_week_for_day(self.athlete2, date(2026, 3, 6))
        planned = PlannedTraining.objects.create(week=week, date=date(2026, 3, 6), day_label="Fri", title="Tempo", notes="", order_in_day=1)
        self.client.login(username="coach2", password="coach2")
        resp = self.client.post(
            reverse("coach_update_planned_training"),
            data=json.dumps({"planned_id": planned.id, "field": "title", "value": "Hacked"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)
        planned.refresh_from_db()
        self.assertNotEqual(planned.title, "Hacked")

    def test_inline_update_rejects_invalid_field(self):
        planned = PlannedTraining.objects.filter(week__training_month__athlete=self.athlete).first()
        self.assertIsNotNone(planned)
        self.client.login(username="coach", password="coach")
        resp = self.client.post(
            reverse("coach_update_planned_training"),
            data=json.dumps({"planned_id": planned.id, "field": "date", "value": "2026-03-10"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_coach_can_update_athlete_focus(self):
        CoachAthlete.objects.get_or_create(coach=self.coach, athlete=self.athlete)
        self.client.login(username="coach", password="coach")
        resp = self.client.post(
            reverse("coach_update_athlete_focus"),
            data=json.dumps({"athlete_id": self.athlete.id, "focus": "Silnicni maraton"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        link = CoachAthlete.objects.get(coach=self.coach, athlete=self.athlete)
        self.assertEqual(link.focus, "Silnicni m")

    def test_other_coach_cannot_update_athlete_focus(self):
        CoachAthlete.objects.get_or_create(coach=self.coach, athlete=self.athlete)
        self.client.login(username="coach2", password="coach2")
        resp = self.client.post(
            reverse("coach_update_athlete_focus"),
            data=json.dumps({"athlete_id": self.athlete.id, "focus": "Test"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_coach_can_reorder_athletes_and_order_is_used_in_sidebar(self):
        CoachAthlete.objects.get_or_create(coach=self.coach, athlete=self.athlete, defaults={"sort_order": 1})
        CoachAthlete.objects.get_or_create(coach=self.coach, athlete=self.athlete2, defaults={"sort_order": 2})
        self.client.login(username="coach", password="coach")
        reorder = self.client.post(
            reverse("coach_reorder_athletes"),
            data=json.dumps({"athlete_ids": [self.athlete2.id, self.athlete.id]}),
            content_type="application/json",
        )
        self.assertEqual(reorder.status_code, 200)
        resp = self.client.get(reverse("coach_training_plans"))
        ordered_ids = [a.id for a in resp.context["athletes"]]
        self.assertGreaterEqual(len(ordered_ids), 3)
        self.assertEqual(ordered_ids[0], self.coach.id)
        self.assertEqual(ordered_ids[1:3], [self.athlete2.id, self.athlete.id])

    def test_coach_reorder_noop_skips_bulk_update(self):
        CoachAthlete.objects.update_or_create(coach=self.coach, athlete=self.athlete, defaults={"sort_order": 1})
        CoachAthlete.objects.update_or_create(coach=self.coach, athlete=self.athlete2, defaults={"sort_order": 2})
        self.client.login(username="coach", password="coach")
        with patch("dashboard.views.CoachAthlete.objects.bulk_update") as bulk_update_mock:
            resp = self.client.post(
                reverse("coach_reorder_athletes"),
                data=json.dumps({"athlete_ids": [self.athlete.id, self.athlete2.id]}),
                content_type="application/json",
            )
        self.assertEqual(resp.status_code, 200)
        bulk_update_mock.assert_not_called()

    def test_coach_can_toggle_athlete_visibility_over_ajax(self):
        CoachAthlete.objects.get_or_create(coach=self.coach, athlete=self.athlete)
        self.client.login(username="coach", password="coach")
        hide_resp = self.client.post(
            reverse("coach_training_plans"),
            data={"action": "hide_athlete", "athlete_id": str(self.athlete.id)},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(hide_resp.status_code, 200)
        self.assertJSONEqual(hide_resp.content, {"ok": True, "hidden": True, "athlete_id": self.athlete.id})
        show_resp = self.client.post(
            reverse("coach_training_plans"),
            data={"action": "show_athlete", "athlete_id": str(self.athlete.id)},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(show_resp.status_code, 200)
        self.assertJSONEqual(show_resp.content, {"ok": True, "hidden": False, "athlete_id": self.athlete.id})

    def test_athlete_can_inline_update_own_planned_training(self):
        planned = PlannedTraining.objects.filter(week__training_month__athlete=self.athlete).first()
        self.assertIsNotNone(planned)
        self.client.login(username="athlete", password="athlete")
        resp = self.client.post(
            reverse("athlete_update_planned_training"),
            data=json.dumps({"planned_id": planned.id, "field": "title", "value": "Own edit"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        planned.refresh_from_db()
        self.assertEqual(planned.title, "Own edit")

    def test_athlete_can_add_second_phase_for_own_day(self):
        planned = PlannedTraining.objects.filter(week__training_month__athlete=self.athlete).first()
        self.assertIsNotNone(planned)
        self.client.login(username="athlete", password="athlete")
        resp = self.client.post(
            reverse("athlete_add_second_phase_training"),
            data=json.dumps({"planned_id": planned.id}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        planned.refresh_from_db()
        self.assertTrue(planned.is_two_phase_day)

    def test_athlete_cannot_inline_update_foreign_planned_training(self):
        foreign_week = _resolve_week_for_day(self.athlete2, date(2026, 3, 7))
        foreign = PlannedTraining.objects.create(week=foreign_week, date=date(2026, 3, 7), day_label="Sat", title="Foreign", order_in_day=1)
        self.client.login(username="athlete", password="athlete")
        resp = self.client.post(
            reverse("athlete_update_planned_training"),
            data=json.dumps({"planned_id": foreign.id, "field": "title", "value": "Hack"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_athlete_cannot_add_second_phase_for_foreign_day(self):
        foreign_week = _resolve_week_for_day(self.athlete2, date(2026, 3, 7))
        foreign = PlannedTraining.objects.create(week=foreign_week, date=date(2026, 3, 7), day_label="Sat", title="Foreign", order_in_day=1)
        self.client.login(username="athlete", password="athlete")
        resp = self.client.post(
            reverse("athlete_add_second_phase_training"),
            data=json.dumps({"planned_id": foreign.id}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_coach_can_add_second_phase_for_accessible_athlete(self):
        planned = PlannedTraining.objects.filter(week__training_month__athlete=self.athlete).first()
        self.assertIsNotNone(planned)
        self.client.login(username="coach", password="coach")
        resp = self.client.post(
            reverse("coach_add_second_phase_training"),
            data=json.dumps({"planned_id": planned.id}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

    def test_coach_cannot_add_second_phase_for_inaccessible_athlete(self):
        week = _resolve_week_for_day(self.athlete2, date(2026, 3, 9))
        planned = PlannedTraining.objects.create(week=week, date=date(2026, 3, 9), day_label="Mon", title="Hard day", order_in_day=1)
        self.client.login(username="coach", password="coach")
        resp = self.client.post(
            reverse("coach_add_second_phase_training"),
            data=json.dumps({"planned_id": planned.id}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_add_second_phase_rejects_duplicate_second_phase(self):
        planned = PlannedTraining.objects.filter(week__training_month__athlete=self.athlete).first()
        self.assertIsNotNone(planned)
        self.client.login(username="athlete", password="athlete")
        first = self.client.post(
            reverse("athlete_add_second_phase_training"),
            data=json.dumps({"planned_id": planned.id}),
            content_type="application/json",
        )
        second = self.client.post(
            reverse("athlete_add_second_phase_training"),
            data=json.dumps({"planned_id": planned.id}),
            content_type="application/json",
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 400)

    def test_athlete_can_remove_second_phase_and_bottom_row_is_deleted(self):
        planned = PlannedTraining.objects.filter(week__training_month__athlete=self.athlete).first()
        self.assertIsNotNone(planned)
        self.client.login(username="athlete", password="athlete")
        create = self.client.post(
            reverse("athlete_add_second_phase_training"),
            data=json.dumps({"planned_id": planned.id}),
            content_type="application/json",
        )
        second_id = create.json()["second_phase_planned_id"]
        remove = self.client.post(
            reverse("athlete_remove_second_phase_training"),
            data=json.dumps({"planned_id": planned.id}),
            content_type="application/json",
        )
        self.assertEqual(remove.status_code, 200)
        self.assertEqual(remove.json()["removed_planned_id"], second_id)

    def test_remove_second_phase_requires_existing_two_phase_day(self):
        planned = PlannedTraining.objects.filter(week__training_month__athlete=self.athlete).first()
        self.assertIsNotNone(planned)
        self.client.login(username="athlete", password="athlete")
        resp = self.client.post(
            reverse("athlete_remove_second_phase_training"),
            data=json.dumps({"planned_id": planned.id}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_coach_can_remove_second_phase_for_accessible_athlete(self):
        planned = PlannedTraining.objects.filter(week__training_month__athlete=self.athlete).first()
        self.assertIsNotNone(planned)
        self.client.login(username="coach", password="coach")
        self.client.post(
            reverse("coach_add_second_phase_training"),
            data=json.dumps({"planned_id": planned.id}),
            content_type="application/json",
        )
        remove = self.client.post(
            reverse("coach_remove_second_phase_training"),
            data=json.dumps({"planned_id": planned.id}),
            content_type="application/json",
        )
        self.assertEqual(remove.status_code, 200)

    def test_coach_update_planned_training_rejects_invalid_session_type(self):
        planned = PlannedTraining.objects.filter(week__training_month__athlete=self.athlete).first()
        self.assertIsNotNone(planned)
        self.client.login(username="coach", password="coach")
        resp = self.client.post(
            reverse("coach_update_planned_training"),
            data=json.dumps({"planned_id": planned.id, "field": "session_type", "value": "BIKE"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
