import json

from django.test import TestCase, override_settings
from django.urls import reverse


class SignupClosedTest(TestCase):
    @override_settings(REGISTRATION_ENABLED=False)
    def test_signup_returns_403_when_disabled(self):
        response = self.client.post(
            reverse("api_auth_signup"),
            data=json.dumps({"email": "x@x.com", "password": "pass", "password_confirmation": "pass"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertIs(response.json()["ok"], False)

    @override_settings(REGISTRATION_ENABLED=True)
    def test_signup_proceeds_to_validation_when_enabled(self):
        response = self.client.post(
            reverse("api_auth_signup"),
            data=json.dumps({}),
            content_type="application/json",
        )
        # form validation kicks in (not 403)
        self.assertEqual(response.status_code, 400)


class SiteConfigViewTest(TestCase):
    def test_returns_registration_enabled_true_by_default(self):
        response = self.client.get(reverse("api_site_config"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("registration_enabled", data)
        self.assertIsInstance(data["registration_enabled"], bool)

    def test_no_auth_required(self):
        response = self.client.get(reverse("api_site_config"))
        self.assertEqual(response.status_code, 200)

    @override_settings(REGISTRATION_ENABLED=False)
    def test_returns_registration_enabled_false_when_disabled(self):
        response = self.client.get(reverse("api_site_config"))
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.json()["registration_enabled"], False)
