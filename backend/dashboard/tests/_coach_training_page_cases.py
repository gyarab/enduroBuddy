from __future__ import annotations

from ._coach_training_base import (
    CoachAthlete,
    CoachJoinRequest,
    TrainingGroup,
    TrainingGroupAthlete,
    TrainingGroupInvite,
    TrainingMonth,
    TrainingWeek,
    override_settings,
    reverse,
    timedelta,
    timezone,
)


class CoachTrainingPageCases:
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

    def test_group_member_without_link_gets_coach_link_on_page_load(self):
        self.assertFalse(CoachAthlete.objects.filter(coach=self.coach, athlete=self.athlete).exists())
        self.client.login(username="coach", password="coach")
        resp = self.client.get(reverse("coach_training_plans"))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(CoachAthlete.objects.filter(coach=self.coach, athlete=self.athlete).exists())

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

    @override_settings(DEBUG=True)
    def test_coach_page_can_render_test_notifications_from_query_param(self):
        self.client.login(username="coach", password="coach")
        resp = self.client.get(reverse("coach_training_plans"), {"test_notifications": "1"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Test: Novy treninkovy plan je pripraven.")

    def test_create_group_action_is_ignored_in_simplified_coach_ui(self):
        self.client.login(username="coach", password="coach")
        resp = self.client.post(
            reverse("coach_training_plans"),
            data={"action": "create_group", "group_name": "Skupina B", "group_description": "Mladez"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(TrainingGroup.objects.filter(coach=self.coach, name="Skupina B").exists())

    def test_create_group_action_does_not_show_legacy_duplicate_error(self):
        self.client.login(username="coach", password="coach")
        resp = self.client.post(
            reverse("coach_training_plans"),
            data={"action": "create_group", "group_name": "skupina a"},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "Skupina s tÃ­mto nÃ¡zvem uÅ¾ existuje.")
        self.assertEqual(TrainingGroup.objects.filter(coach=self.coach).count(), 1)

    def test_coach_can_create_group_invite(self):
        self.client.login(username="coach", password="coach")
        resp = self.client.post(
            reverse("coach_training_plans"),
            data={"action": "create_invite", "group_id": str(self.group.id), "invited_email": "athlete2@example.com"},
        )
        self.assertEqual(resp.status_code, 302)
        invite = TrainingGroupInvite.objects.get(group=self.group)
        self.assertEqual(invite.created_by_id, self.coach.id)
        self.assertEqual(invite.invited_email, "athlete2@example.com")
        self.assertTrue(invite.token)

    def test_coach_can_bulk_add_next_month_with_full_weeks_for_all_athletes(self):
        CoachAthlete.objects.get_or_create(coach=self.coach, athlete=self.athlete2)
        self.client.login(username="coach", password="coach")
        resp = self.client.post(reverse("coach_training_plans"), data={"action": "bulk_add_next_month"})
        self.assertEqual(resp.status_code, 302)

        next_month_athlete2 = TrainingMonth.objects.filter(athlete=self.athlete2).order_by("-year", "-month").first()
        self.assertIsNotNone(next_month_athlete2)
        weeks = TrainingWeek.objects.filter(training_month=next_month_athlete2).order_by("week_index")
        self.assertGreaterEqual(weeks.count(), 4)
        for week in weeks:
            self.assertEqual(week.planned_trainings.count(), 7)

        self.assertGreaterEqual(TrainingMonth.objects.filter(athlete=self.athlete).count(), 2)
        self.assertEqual(TrainingMonth.objects.filter(athlete=self.athlete2).count(), 1)

    def test_athlete_can_accept_invite_and_is_linkED_to_group_and_coach(self):
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
        resp = self.client.post(reverse("dashboard_home"), data={"action": "request_coach_by_code", "coach_code": "abc123"})
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
            data={"action": "approve_join_request", "join_request_id": str(join_request.id)},
        )
        self.assertEqual(resp.status_code, 302)
        join_request.refresh_from_db()
        self.assertEqual(join_request.status, CoachJoinRequest.Status.APPROVED)
        self.assertTrue(CoachAthlete.objects.filter(coach=self.coach, athlete=self.athlete2).exists())

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
