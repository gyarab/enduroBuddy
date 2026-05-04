from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import ImportJob


class Command(BaseCommand):
    help = "Přepíše ImportJoby ve stavu RUNNING na ERROR (cleanup po restartu workeru)."

    def handle(self, *args, **options):
        updated = ImportJob.objects.filter(
            status=ImportJob.Status.RUNNING,
        ).update(
            status=ImportJob.Status.ERROR,
            message="Worker restarted",
            finished_at=timezone.now(),
        )
        self.stdout.write(f"Reset {updated} stale import job(s).")
