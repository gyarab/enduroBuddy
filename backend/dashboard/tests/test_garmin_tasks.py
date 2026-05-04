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


def test_execute_garmin_sync_job_marks_success(import_job):
    """Job musí skončit SUCCESS po úspěšném sync."""
    from dashboard.services.tasks import _execute_garmin_sync_job

    with patch("dashboard.services.tasks.sync_garmin_for_user") as mock_sync, \
         patch("dashboard.services.imports.audit_garmin"):
        mock_sync.return_value = (5, 2, MagicMock())
        _execute_garmin_sync_job(import_job.id)

    import_job.refresh_from_db()
    assert import_job.status == ImportJob.Status.SUCCESS
    assert import_job.imported_count == 5
    assert import_job.skipped_count == 2


@pytest.mark.django_db
def test_execute_garmin_sync_job_nonexistent_id():
    """Task s neexistujícím job ID musí tiše skončit bez výjimky."""
    from dashboard.services.tasks import _execute_garmin_sync_job
    _execute_garmin_sync_job(999999)


def test_enqueue_garmin_sync_job_calls_async_task(import_job):
    """enqueue_garmin_sync_job musí volat async_task s _execute_garmin_sync_job."""
    from dashboard.services.tasks import enqueue_garmin_sync_job, _execute_garmin_sync_job

    with patch("dashboard.services.tasks.async_task") as mock_async_task:
        enqueue_garmin_sync_job(import_job.id)
        mock_async_task.assert_called_once_with(_execute_garmin_sync_job, import_job.id)
