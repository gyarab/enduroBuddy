from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import CoachJoinRequest, Role


class ProfileManageTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="athlete-profile",
            password="old-pass-123",
            first_name="Old",
            last_name="Name",
        )
        self.coach = User.objects.create_user(username="coach-profile", password="coach-pass-123")
        self.coach.profile.role = Role.COACH
        self.coach.profile.coach_join_code = "ABC123XYZ789"
        self.coach.profile.save(update_fields=["role", "coach_join_code"])
        self.client.login(username="athlete-profile", password="old-pass-123")

    def test_update_profile_updates_first_and_last_name(self):
        response = self.client.post(
            reverse("profile_manage"),
            data={
                "action": "update_profile",
                "first_name": "New",
                "last_name": "Runner",
                "next": reverse("dashboard_home"),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "New")
        self.assertEqual(self.user.last_name, "Runner")

    def test_change_password_updates_password_and_keeps_session(self):
        response = self.client.post(
            reverse("profile_manage"),
            data={
                "action": "change_password",
                "old_password": "old-pass-123",
                "new_password": "new-pass-12345",
                "new_password_confirm": "new-pass-12345",
                "next": reverse("dashboard_home"),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new-pass-12345"))

        dashboard_response = self.client.get(reverse("dashboard_home"))
        self.assertEqual(dashboard_response.status_code, 200)

    def test_request_coach_by_code_creates_pending_request(self):
        response = self.client.post(
            reverse("profile_manage"),
            data={
                "action": "request_coach_by_code",
                "coach_code": "abc123xyz789",
                "next": reverse("dashboard_home"),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            CoachJoinRequest.objects.filter(
                coach=self.coach,
                athlete=self.user,
                status=CoachJoinRequest.Status.PENDING,
            ).exists()
        )
