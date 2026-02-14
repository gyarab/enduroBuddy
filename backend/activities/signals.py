from __future__ import annotations

import os

from django.db.models.signals import post_save
from django.dispatch import receiver

from activities.models import ActivityFile
from activities.services.fit_importer import import_fit_into_activity


@receiver(post_save, sender=ActivityFile)
def parse_fit_on_upload(sender, instance: ActivityFile, created: bool, **kwargs):
    if not created:
        return
    if instance.file_type != ActivityFile.FileType.FIT:
        return
    if not instance.file:
        return

    # parse z file objektu (bez nutnosti path)
    import_fit_into_activity(
        activity=instance.activity,
        fileobj=instance.file.file,
        original_name=instance.original_name or (instance.file.name or ""),
        create_activity_file_row=False,  # už existuje instance
    )

    # po úspěchu smaž fyzický soubor a vyprázdni field
    try:
        path = instance.file.path
    except Exception:
        path = None

    # vyprázdni FileField v DB
    instance.file.delete(save=False)  # zkusí smazat i storage
    instance.file = None
    instance.save(update_fields=["file"])

    # fallback: kdyby storage nesmazal
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass
