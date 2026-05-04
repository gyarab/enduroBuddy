import json

from django.test import TestCase, override_settings
from django.urls import reverse


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
