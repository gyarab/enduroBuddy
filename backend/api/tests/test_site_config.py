from django.test import TestCase, override_settings
from django.urls import reverse


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
