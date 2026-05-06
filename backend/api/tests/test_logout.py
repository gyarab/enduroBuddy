from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


class LogoutEndpointTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="logout-test",
            email="logout@example.com",
            password="pass-123",
        )

    def test_logout_clears_session_for_authenticated_user(self):
        self.client.login(username="logout-test", password="pass-123")
        self.assertIn("_auth_user_id", self.client.session)

        response = self.client.post(reverse("api_auth_logout"))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_succeeds_without_csrf_token(self):
        """Logout must work even when the CSRF token is absent or wrong.

        This covers the production bug where getCsrfToken() returns null in
        certain cross-domain or cookie-domain edge cases, causing the logout
        POST to be rejected by CSRF middleware and the session to survive.
        """
        self.client.login(username="logout-test", password="pass-123")
        csrf_client = Client(enforce_csrf_checks=True)
        # Carry the session cookie over but send NO X-CSRFToken header
        csrf_client.cookies = self.client.cookies

        response = csrf_client.post(
            reverse("api_auth_logout"),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])

    def test_logout_returns_login_redirect(self):
        self.client.login(username="logout-test", password="pass-123")
        response = self.client.post(reverse("api_auth_logout"))
        data = response.json()
        self.assertIn("/accounts/login/", data["redirect_to"])

    def test_logout_unauthenticated_still_returns_ok(self):
        response = self.client.post(reverse("api_auth_logout"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
