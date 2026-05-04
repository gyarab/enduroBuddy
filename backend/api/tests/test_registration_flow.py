import json

from django.test import TestCase, override_settings
from django.urls import reverse
from allauth.socialaccount.models import SocialAccount


VALID_SIGNUP = {
    "email": "newuser@example.com",
    "first_name": "Test",
    "last_name": "User",
    "role": "ATHLETE",
    "password": "StrongPass123!",
    "password_confirmation": "StrongPass123!",
    "terms_accepted": True,
}


class SignupTermsValidationTest(TestCase):
    @override_settings(REGISTRATION_ENABLED=True)
    def test_signup_without_terms_returns_400(self):
        payload = {**VALID_SIGNUP, "terms_accepted": False}
        response = self.client.post(
            reverse("api_auth_signup"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("terms_accepted", response.json()["errors"])

    @override_settings(REGISTRATION_ENABLED=True)
    def test_signup_missing_terms_field_returns_400(self):
        payload = {k: v for k, v in VALID_SIGNUP.items() if k != "terms_accepted"}
        response = self.client.post(
            reverse("api_auth_signup"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("terms_accepted", response.json()["errors"])

    @override_settings(REGISTRATION_ENABLED=True)
    def test_signup_with_terms_saves_terms_accepted_at(self):
        from django.contrib.auth import get_user_model
        response = self.client.post(
            reverse("api_auth_signup"),
            data=json.dumps(VALID_SIGNUP),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        User = get_user_model()
        user = User.objects.get(email=VALID_SIGNUP["email"])
        self.assertIsNotNone(user.profile.terms_accepted_at)


class ProfileSetupEndpointTest(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="google_user",
            email="google@example.com",
            password="unused",
        )
        SocialAccount.objects.create(user=self.user, provider="google", uid="google-uid-123")

    def test_profile_setup_requires_authentication(self):
        response = self.client.post(
            "/api/v1/auth/profile-setup/",
            data=json.dumps({"role": "ATHLETE", "terms_accepted": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_profile_setup_saves_role_and_terms(self):
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/v1/auth/profile-setup/",
            data=json.dumps({
                "first_name": "Jan",
                "last_name": "Novák",
                "role": "ATHLETE",
                "terms_accepted": True,
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertIn("redirect_to", data)

        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, "Jan")
        self.assertEqual(self.user.last_name, "Novák")
        self.assertEqual(self.user.profile.role, "ATHLETE")
        self.assertTrue(self.user.profile.google_role_confirmed)
        self.assertIsNotNone(self.user.profile.terms_accepted_at)

    def test_profile_setup_marks_google_role_confirmed(self):
        self.client.force_login(self.user)
        self.assertFalse(self.user.profile.google_role_confirmed)
        self.client.post(
            "/api/v1/auth/profile-setup/",
            data=json.dumps({"role": "COACH", "terms_accepted": True}),
            content_type="application/json",
        )
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.google_role_confirmed)

    def test_profile_setup_requires_terms(self):
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/v1/auth/profile-setup/",
            data=json.dumps({"role": "ATHLETE", "terms_accepted": False}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("terms_accepted", response.json()["errors"])

    def test_profile_setup_requires_valid_role(self):
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/v1/auth/profile-setup/",
            data=json.dumps({"role": "INVALID", "terms_accepted": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("role", response.json()["errors"])

    def test_profile_setup_not_needed_for_email_user(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        email_user = User.objects.create_user(
            username="emailuser",
            email="emailonly@example.com",
            password="pass",
        )
        self.client.force_login(email_user)
        response = self.client.post(
            "/api/v1/auth/profile-setup/",
            data=json.dumps({"role": "ATHLETE", "terms_accepted": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)


class AuthMeNeedsProfileSetupTest(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        self.User = get_user_model()

    def test_auth_me_includes_needs_profile_setup_false_for_email_user(self):
        user = self.User.objects.create_user(
            username="emailme",
            email="emailme@example.com",
            password="pass",
        )
        self.client.force_login(user)
        response = self.client.get(reverse("api_auth_me"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["needs_profile_setup"])

    def test_auth_me_includes_needs_profile_setup_true_for_google_user(self):
        user = self.User.objects.create_user(
            username="googleme",
            email="googleme@example.com",
            password="pass",
        )
        SocialAccount.objects.create(user=user, provider="google", uid="uid-456")
        self.client.force_login(user)
        response = self.client.get(reverse("api_auth_me"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["needs_profile_setup"])
