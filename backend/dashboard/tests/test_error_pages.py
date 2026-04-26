from __future__ import annotations

from django.test import SimpleTestCase, override_settings


@override_settings(DEBUG=False)
class ErrorHandlerTests(SimpleTestCase):
    def test_api_404_returns_json(self):
        response = self.client.get("/api/v1/nonexistent-route-abc123/")

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data)

    def test_browser_404_returns_html_without_bootstrap(self):
        response = self.client.get("/missing-page-for-error-handler-check/")

        self.assertEqual(response.status_code, 404)
        body = response.content.decode("utf-8")
        self.assertIn("Stránka nenalezena", body)
        self.assertNotIn("bootstrap", body.lower())

    def test_browser_404_html_is_self_contained(self):
        response = self.client.get("/missing-page-for-error-handler-check/")

        body = response.content.decode("utf-8")
        self.assertIn("<html", body)
        self.assertIn("EnduroBuddy", body)


@override_settings(DEBUG=True)
class ErrorPreviewPageTests(SimpleTestCase):
    def test_error_preview_index_is_available_in_debug(self):
        response = self.client.get("/__debug/ui/errors/")

        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8")
        self.assertIn("/__debug/ui/errors/404/", body)
        self.assertIn("/accounts/social/login/error/", body)

    def test_error_preview_status_page_renders(self):
        response = self.client.get("/__debug/ui/errors/500/")

        self.assertEqual(response.status_code, 500)
        body = response.content.decode("utf-8")
        self.assertIn("Něco se pokazilo", body)
        self.assertNotIn("bootstrap", body.lower())
