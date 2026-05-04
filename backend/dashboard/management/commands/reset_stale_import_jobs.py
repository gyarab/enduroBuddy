from django.core.management.base import BaseCommand

from accounts.models import ImportJob


class Command(BaseCommand):
    help = "Přepíše ImportJoby ve stavu RUNNING na ERROR (cleanup po restartu workeru)."

    def handle(self, *args, **options):
        updated = ImportJob.objects.filter(
            status=ImportJob.Status.RUNNING,
        ).update(
            status=ImportJob.Status.ERROR,
            message="Worker restarted",
        )
        self.stdout.write(f"Reset {updated} stale import job(s).")
