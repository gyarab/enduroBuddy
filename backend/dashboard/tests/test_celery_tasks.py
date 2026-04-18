from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from accounts.models import ImportJob


@pytest.fixture
def import_job(db, django_user_model):
    user = django_user_model.objects.create_user(
        username="tester@example.com",
        email="tester@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )
    return ImportJob.objects.create(
        user=user,
        kind=ImportJob.Kind.GARMIN_SYNC,
        status=ImportJob.Status.QUEUED,
        window="last_7_days",
        message="Waiting.",
    )


def test_execute_garmin_sync_job_marks_success(import_job):
    """Job musí skončit SUCCESS po úspěšném sync."""
    from dashboard.services.tasks import _execute_garmin_sync_job

    with patch("dashboard.services.tasks.sync_garmin_for_user") as mock_sync:
        mock_sync.return_value = (5, 2, MagicMock())
        _execute_garmin_sync_job(import_job.id)

    import_job.refresh_from_db()
    assert import_job.status == ImportJob.Status.SUCCESS
    assert import_job.imported_count == 5
    assert import_job.skipped_count == 2


def test_execute_garmin_sync_job_nonexistent_id():
    """Task s neexistujícím job ID musí tiše skončit bez výjimky."""
    from dashboard.services.tasks import _execute_garmin_sync_job
    _execute_garmin_sync_job(999999)  # nesmí vyhodit výjimku


def test_enqueue_garmin_sync_job_uses_celery(import_job):
    """enqueue_garmin_sync_job musí volat Celery task .delay(), ne ThreadPoolExecutor."""
    from dashboard.services import tasks as tasks_module

    with patch.object(tasks_module, "execute_garmin_sync_job") as mock_task:
        mock_task.delay = MagicMock()
        from dashboard.services.tasks import enqueue_garmin_sync_job
        enqueue_garmin_sync_job(import_job.id)
        mock_task.delay.assert_called_once_with(import_job.id)
