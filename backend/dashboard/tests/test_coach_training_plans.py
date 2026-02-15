from __future__ import annotations

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import CoachAthlete, Role, TrainingGroup, TrainingGroupAthlete, TrainingGroupInvite
from dashboard.views import _resolve_week_for_day
from training.models import PlannedTraining, TrainingMonth, TrainingWeek


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
        self.assertEqual(resp.context["selected_athlete"].id, self.athlete.id)
        self.assertGreaterEqual(len(resp.context["month_cards"]), 1)

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

