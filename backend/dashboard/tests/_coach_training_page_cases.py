from __future__ import annotations

from ._coach_training_base import (
    AppNotification,
    CoachAthlete,
    CoachJoinRequest,
    TrainingGroup,
    TrainingGroupAthlete,
    TrainingGroupInvite,
    TrainingMonth,
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
        self.assertContains(resp, "Test: Nový tréninkový plán je připraven.")

    @override_settings(DEBUG=True)
    def test_coach_page_can_render_full_test_notification_suite_from_query_param(self):
        self.client.login(username="coach", password="coach")
        resp = self.client.get(reverse("coach_training_plans"), {"test_notifications": "all"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "ebTestClientNotifications")
        self.assertContains(resp, "Test client:")

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

    def test_coach_manage_modal_uses_code_flow_instead_of_invites(self):
        self.client.login(username="coach", password="coach")
        resp = self.client.get(reverse("coach_training_plans"))
        self.coach.profile.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Kód trenéra")
        self.assertContains(resp, self.coach.profile.coach_join_code)
        self.assertNotContains(resp, "Vytvořit odkaz pozvánky")

    def test_coach_page_shows_add_month_button_for_selected_plan(self):
        self.client.login(username="coach", password="coach")
        own_resp = self.client.get(reverse("coach_training_plans"))
        self.assertEqual(own_resp.status_code, 200)
        self.assertContains(own_resp, 'name="action" value="add_next_month_selected"')

        athlete_resp = self.client.get(reverse("coach_training_plans"), {"athlete": self.athlete.id})
        self.assertEqual(athlete_resp.status_code, 200)
        self.assertContains(athlete_resp, 'name="action" value="add_next_month_selected"')

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

    def test_coach_page_renders_persistent_join_request_notification(self):
        notification = AppNotification.objects.create(
            recipient=self.coach,
            actor=self.athlete2,
            kind=AppNotification.Kind.COACH_JOIN_REQUEST,
            tone=AppNotification.Tone.INFO,
            text="Nová žádost o trénování od athlete2.",
        )
        self.client.login(username="coach", password="coach")

        response = self.client.get(reverse("coach_training_plans"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, notification.text)
        self.assertContains(response, f'data-app-notification-id="{notification.id}"')

    def test_join_request_creation_creates_persistent_notification_for_coach(self):
        self.coach.profile.coach_join_code = "ABC123"
        self.coach.profile.save(update_fields=["coach_join_code"])
        self.client.login(username="athlete2", password="athlete2")
        response = self.client.post(reverse("dashboard_home"), data={"action": "request_coach_by_code", "coach_code": "abc123"})
        self.assertEqual(response.status_code, 302)
        notification = AppNotification.objects.filter(recipient=self.coach).order_by("-id").first()
        self.assertIsNotNone(notification)
        self.assertIn("Nová žádost o trénování", notification.text)

    def test_notification_poll_returns_unread_notifications(self):
        AppNotification.objects.create(
            recipient=self.coach,
            actor=self.athlete2,
            kind=AppNotification.Kind.COACH_JOIN_REQUEST,
            tone=AppNotification.Tone.INFO,
            text="Nová žádost o trénování od athlete2.",
        )
        self.client.login(username="coach", password="coach")
        response = self.client.get(reverse("notification_poll"), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(len(payload["notifications"]), 1)
        self.assertIn("Nová žádost o trénování", payload["notifications"][0]["text"])

    def test_notification_mark_read_marks_only_current_users_notifications(self):
        own = AppNotification.objects.create(
            recipient=self.coach,
            actor=self.athlete2,
            kind=AppNotification.Kind.COACH_JOIN_REQUEST,
            tone=AppNotification.Tone.INFO,
            text="Nová žádost o trénování od athlete2.",
        )
        foreign = AppNotification.objects.create(
            recipient=self.other_coach,
            actor=self.athlete,
            kind=AppNotification.Kind.COACH_JOIN_REQUEST,
            tone=AppNotification.Tone.INFO,
            text="Nová žádost o trénování od athlete.",
        )
        self.client.login(username="coach", password="coach")
        response = self.client.post(
            reverse("notification_mark_read"),
            data='{"notification_ids": [%d, %d]}' % (own.id, foreign.id),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        own.refresh_from_db()
        foreign.refresh_from_db()
        self.assertIsNotNone(own.read_at)
        self.assertIsNone(foreign.read_at)

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
