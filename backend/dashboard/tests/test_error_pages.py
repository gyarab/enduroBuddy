from __future__ import annotations

from django.test import SimpleTestCase, override_settings


@override_settings(DEBUG=True)
class ErrorPreviewPageTests(SimpleTestCase):
    def test_error_preview_index_is_available_in_debug(self):
        response = self.client.get("/__debug/ui/errors/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "UI fallback preview")
        self.assertContains(response, "/__debug/ui/errors/404/")
        self.assertContains(response, "/accounts/social/login/error/")

    def test_error_preview_status_page_renders_bootstrap_fallback(self):
        response = self.client.get("/__debug/ui/errors/500/")

        self.assertEqual(response.status_code, 500)
        body = response.content.decode("utf-8")
        self.assertIn("Něco se pokazilo", body)
        self.assertIn("debug preview", body)


@override_settings(DEBUG=False)
class ErrorHandlerPageTests(SimpleTestCase):
    def test_unknown_route_uses_custom_404_template(self):
        response = self.client.get("/missing-page-for-error-handler-check/")

        self.assertEqual(response.status_code, 404)
        body = response.content.decode("utf-8")
        self.assertIn("Stránka nenalezena", body)
        self.assertIn("EnduroBuddy", body)
