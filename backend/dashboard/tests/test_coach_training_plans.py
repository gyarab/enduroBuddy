from __future__ import annotations

import json
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import CoachAthlete, CoachJoinRequest, Role, TrainingGroup, TrainingGroupAthlete, TrainingGroupInvite
from dashboard.views import _resolve_week_for_day
from training.models import CompletedTraining, PlannedTraining, TrainingMonth, TrainingWeek


class CoachTrainingPlansTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.coach = User.objects.create_user(username="coach", password="coach")
        self.athlete = User.objects.create_user(username="athlete", password="athlete")
        self.athlete2 = User.objects.create_user(username="athlete2", password="athlete2")
        self.other_coach = User.objects.create_user(username="coach2", password="coach2")

        self.coach.profile.role = Role.COACH
        self.coach.profile.save(update_fields=["role"])

        self.other_coach.profile.role = Role.COACH
        self.other_coach.profile.save(update_fields=["role"])

        self.group = TrainingGroup.objects.create(coach=self.coach, name="Skupina A")
        TrainingGroupAthlete.objects.create(group=self.group, athlete=self.athlete)

        self.other_group = TrainingGroup.objects.create(coach=self.other_coach, name="Cizi skupina")
        TrainingGroupAthlete.objects.create(group=self.other_group, athlete=self.athlete)

        week = _resolve_week_for_day(self.athlete, date(2026, 3, 5))
        PlannedTraining.objects.create(
            week=week,
            date=date(2026, 3, 5),
            day_label="Thu",
            title="Easy run",
            order_in_day=1,
        )

    def test_non_coach_is_redirected(self):
        self.client.login(username="athlete", password="athlete")
        resp = self.client.get(reverse("coach_training_plans"))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("dashboard_home"))

    def test_coach_sees_own_group_and_athlete_dashboard(self):
        self.client.login(username="coach", password="coach")
        resp = self.client.get(reverse("coach_training_plans"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["selected_group"].id, self.group.id)
        self.assertEqual(resp.context["selected_athlete"].id, self.coach.id)
        self.assertTrue(resp.context["selected_athlete_is_self"])
        self.assertGreaterEqual(len(resp.context["month_cards"]), 0)

    def test_coach_cannot_select_foreign_group(self):
        self.client.login(username="coach", password="coach")
        resp = self.client.get(reverse("coach_training_plans"), {"group": str(self.other_group.id)})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["selected_group"].id, self.group.id)

    def test_coach_button_is_visible_in_navbar_on_dashboard(self):
        self.client.login(username="coach", password="coach")
        resp = self.client.get(reverse("dashboard_home"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, reverse("coach_training_plans"))

    def test_create_group_action_is_ignored_in_simplified_coach_ui(self):
        self.client.login(username="coach", password="coach")
        resp = self.client.post(
            reverse("coach_training_plans"),
            data={
                "action": "create_group",
                "group_name": "Skupina B",
                "group_description": "Mladez",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(TrainingGroup.objects.filter(coach=self.coach, name="Skupina B").exists())

    def test_create_group_action_does_not_show_legacy_duplicate_error(self):
        self.client.login(username="coach", password="coach")
        resp = self.client.post(
            reverse("coach_training_plans"),
            data={
                "action": "create_group",
                "group_name": "skupina a",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "Skupina s tímto názvem už existuje.")
        self.assertEqual(TrainingGroup.objects.filter(coach=self.coach).count(), 1)

    def test_coach_can_create_group_invite(self):
        self.client.login(username="coach", password="coach")
        resp = self.client.post(
            reverse("coach_training_plans"),
            data={
                "action": "create_invite",
                "group_id": str(self.group.id),
                "invited_email": "athlete2@example.com",
            },
        )
        self.assertEqual(resp.status_code, 302)
        invite = TrainingGroupInvite.objects.get(group=self.group)
        self.assertEqual(invite.created_by_id, self.coach.id)
        self.assertEqual(invite.invited_email, "athlete2@example.com")
        self.assertTrue(invite.token)

    def test_coach_can_bulk_add_next_month_with_full_weeks_for_all_athletes(self):
        CoachAthlete.objects.get_or_create(coach=self.coach, athlete=self.athlete2)

        self.client.login(username="coach", password="coach")
        resp = self.client.post(
            reverse("coach_training_plans"),
            data={
                "action": "bulk_add_next_month",
            },
        )
        self.assertEqual(resp.status_code, 302)

        next_month_athlete2 = (
            TrainingMonth.objects.filter(athlete=self.athlete2).order_by("-year", "-month").first()
        )
        self.assertIsNotNone(next_month_athlete2)
        weeks = TrainingWeek.objects.filter(training_month=next_month_athlete2).order_by("week_index")
        self.assertGreaterEqual(weeks.count(), 4)

        for week in weeks:
            self.assertEqual(week.planned_trainings.count(), 7)

        self.assertGreaterEqual(TrainingMonth.objects.filter(athlete=self.athlete).count(), 2)
        self.assertEqual(TrainingMonth.objects.filter(athlete=self.athlete2).count(), 1)

    def test_athlete_can_accept_invite_and_is_linked_to_group_and_coach(self):
        invite = TrainingGroupInvite.objects.create(
            group=self.group,
            created_by=self.coach,
            token="token-123",
            expires_at=timezone.now() + timedelta(days=7),
        )

        self.client.login(username="athlete2", password="athlete2")
        resp = self.client.post(reverse("training_group_invite_accept", args=[invite.token]))
        self.assertEqual(resp.status_code, 302)

        self.assertTrue(TrainingGroupAthlete.objects.filter(group=self.group, athlete=self.athlete2).exists())
        self.assertTrue(CoachAthlete.objects.filter(coach=self.coach, athlete=self.athlete2).exists())
        invite.refresh_from_db()
        self.assertEqual(invite.used_by_id, self.athlete2.id)
        self.assertIsNotNone(invite.used_at)

    def test_athlete_can_request_coach_by_code(self):
        self.coach.profile.coach_join_code = "ABC123"
        self.coach.profile.save(update_fields=["coach_join_code"])

        self.client.login(username="athlete2", password="athlete2")
        resp = self.client.post(
            reverse("dashboard_home"),
            data={
                "action": "request_coach_by_code",
                "coach_code": "abc123",
            },
        )
        self.assertEqual(resp.status_code, 302)
        req = CoachJoinRequest.objects.filter(coach=self.coach, athlete=self.athlete2, status=CoachJoinRequest.Status.PENDING).first()
        self.assertIsNotNone(req)

    def test_coach_can_approve_join_request(self):
        join_request = CoachJoinRequest.objects.create(
            coach=self.coach,
            athlete=self.athlete2,
            status=CoachJoinRequest.Status.PENDING,
        )

        self.client.login(username="coach", password="coach")
        resp = self.client.post(
            reverse("coach_training_plans"),
            data={
                "action": "approve_join_request",
                "join_request_id": str(join_request.id),
            },
        )
        self.assertEqual(resp.status_code, 302)
        join_request.refresh_from_db()
        self.assertEqual(join_request.status, CoachJoinRequest.Status.APPROVED)
        self.assertTrue(CoachAthlete.objects.filter(coach=self.coach, athlete=self.athlete2).exists())

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

    def test_coach_can_inline_update_own_planned_training(self):
        own_week = _resolve_week_for_day(self.coach, date(2026, 3, 8))
        own_planned = PlannedTraining.objects.create(
            week=own_week,
            date=date(2026, 3, 8),
            day_label="Sun",
            title="Coach base run",
            notes="",
            order_in_day=1,
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
        planned = PlannedTraining.objects.create(
            week=week,
            date=date(2026, 3, 6),
            day_label="Fri",
            title="Tempo",
            notes="",
            order_in_day=1,
        )
        self.assertIsNotNone(planned)

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

    def test_coach_can_toggle_athlete_visibility_over_ajax(self):
        CoachAthlete.objects.get_or_create(coach=self.coach, athlete=self.athlete)
        self.client.login(username="coach", password="coach")

        hide_resp = self.client.post(
            reverse("coach_training_plans"),
            data={"action": "hide_athlete", "athlete_id": str(self.athlete.id)},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(hide_resp.status_code, 200)
        self.assertJSONEqual(
            hide_resp.content,
            {"ok": True, "hidden": True, "athlete_id": self.athlete.id},
        )
        link = CoachAthlete.objects.get(coach=self.coach, athlete=self.athlete)
        self.assertTrue(link.hidden_from_plans)

        show_resp = self.client.post(
            reverse("coach_training_plans"),
            data={"action": "show_athlete", "athlete_id": str(self.athlete.id)},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(show_resp.status_code, 200)
        self.assertJSONEqual(
            show_resp.content,
            {"ok": True, "hidden": False, "athlete_id": self.athlete.id},
        )
        link.refresh_from_db()
        self.assertFalse(link.hidden_from_plans)

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

    def test_athlete_cannot_inline_update_foreign_planned_training(self):
        foreign_week = _resolve_week_for_day(self.athlete2, date(2026, 3, 7))
        foreign = PlannedTraining.objects.create(
            week=foreign_week,
            date=date(2026, 3, 7),
            day_label="Sat",
            title="Foreign",
            order_in_day=1,
        )

        self.client.login(username="athlete", password="athlete")
        resp = self.client.post(
            reverse("athlete_update_planned_training"),
            data=json.dumps({"planned_id": foreign.id, "field": "title", "value": "Hack"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_coach_can_inline_update_completed_training(self):
        planned = PlannedTraining.objects.filter(week__training_month__athlete=self.athlete).first()
        self.assertIsNotNone(planned)

        self.client.login(username="coach", password="coach")
        resp = self.client.post(
            reverse("coach_update_completed_training"),
            data=json.dumps({"planned_id": planned.id, "field": "km", "value": "8.50"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

        completed = CompletedTraining.objects.get(planned=planned)
        self.assertEqual(completed.distance_m, 8500)

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

    def test_athlete_can_add_next_month_from_dashboard(self):
        self.client.login(username="athlete", password="athlete")
        before = TrainingMonth.objects.filter(athlete=self.athlete).count()
        resp = self.client.post(reverse("dashboard_home"), data={"action": "add_next_month_self"})
        self.assertEqual(resp.status_code, 302)
        after = TrainingMonth.objects.filter(athlete=self.athlete).count()
        self.assertGreaterEqual(after, before + 1)

    def test_coach_can_add_next_month_for_selected_athlete(self):
        self.client.login(username="coach", password="coach")
        before = TrainingMonth.objects.filter(athlete=self.athlete).count()
        resp = self.client.post(
            reverse("coach_training_plans"),
            data={"action": "add_next_month_selected", "athlete_id": str(self.athlete.id)},
        )
        self.assertEqual(resp.status_code, 302)
        after = TrainingMonth.objects.filter(athlete=self.athlete).count()
        self.assertGreaterEqual(after, before + 1)
