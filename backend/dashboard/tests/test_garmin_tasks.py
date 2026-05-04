from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from accounts.models import ImportJob


@pytest.fixture
def garmin_user(db, django_user_model):
    return django_user_model.objects.create_user(
        username="tester@example.com",
        email="tester@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def import_job(garmin_user):
    return ImportJob.objects.create(
        user=garmin_user,
        kind=ImportJob.Kind.GARMIN_SYNC,
        status=ImportJob.Status.QUEUED,
        window="last_7_days",
        message="Waiting.",
    )


def test_reset_stale_import_jobs_marks_running_as_error(garmin_user):
    """reset_stale_import_jobs musí přepsat RUNNING joby na ERROR."""
    from django.core.management import call_command

    job = ImportJob.objects.create(
        user=garmin_user,
        kind=ImportJob.Kind.GARMIN_SYNC,
        status=ImportJob.Status.RUNNING,
        window="last_7_days",
        message="Running.",
    )
    call_command("reset_stale_import_jobs")
    job.refresh_from_db()
    assert job.status == ImportJob.Status.ERROR
    assert job.message == "Worker restarted"


def test_reset_stale_import_jobs_ignores_non_running(garmin_user):
    """reset_stale_import_jobs nesmí měnit joby mimo stav RUNNING."""
    from django.core.management import call_command

    job = ImportJob.objects.create(
        user=garmin_user,
        kind=ImportJob.Kind.GARMIN_SYNC,
        status=ImportJob.Status.QUEUED,
        window="last_7_days",
        message="Waiting.",
    )
    call_command("reset_stale_import_jobs")
    job.refresh_from_db()
    assert job.status == ImportJob.Status.QUEUED
