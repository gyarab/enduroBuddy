from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import GarminConnection, GarminSyncAudit, ImportJob
from accounts.services.garmin_secret_store import encrypt_tokenstore
from activities.models import Activity, ActivityFile, ActivityImportLedger, ActivityInterval
from activities.services.garmin_importer import GarminDownloadResult, GarminFitPayload
from activities.services.fit_parser import parse_fit_file
from dashboard.services.imports import _resolve_planned_training, _select_payloads_for_import
from dashboard.views import _resolve_week_for_day
from training.models import CompletedTraining, PlannedTraining, TrainingMonth, TrainingWeek


FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "activities" / "tests" / "fixtures" / "fit"
TEST_KMS_KEY = "IO1tJrYVYrSgHUy4iJ5wsIXv89hRiYxYEyg2asOlVtE="


@override_settings(
    GARMIN_KMS_KEYS=TEST_KMS_KEY,
    GARMIN_KMS_KEY_ID="test-kms",
    GARMIN_CONNECT_ENABLED=True,
    GARMIN_SYNC_ENABLED=True,
)
class DashboardFitImportBase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="runner", password="runner")
        self.client.login(username="runner", password="runner")

    def _connect_garmin(self, tokenstore: str = "dummy-tokenstore"):
        return GarminConnection.objects.create(
            user=self.user,
            garmin_email="runner@example.com",
            garmin_display_name="runner",
            encrypted_tokenstore=encrypt_tokenstore(tokenstore),
            kms_key_id="test-kms",
            is_active=True,
        )
