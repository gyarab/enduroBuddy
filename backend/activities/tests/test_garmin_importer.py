from __future__ import annotations

from django.test import SimpleTestCase
from unittest.mock import Mock, patch

from activities.services.garmin_importer import GarminImportError, connect_garmin_account


class GarminImporterTests(SimpleTestCase):
    @patch("activities.services.garmin_importer._new_client")
    def test_connect_garmin_account_reports_mfa_requirement(self, new_client_mock):
        fake_client = Mock()
        fake_client.login.return_value = ("needs_mfa", {"client": "state"})
        new_client_mock.return_value = fake_client

        with self.assertRaisesMessage(GarminImportError, "requires MFA verification"):
            connect_garmin_account(email="user@example.com", password="secret")

