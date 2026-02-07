from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ActivityFile, ActivityInterval


@receiver(post_save, sender=ActivityFile)
def parse_fit_on_upload(sender, instance: ActivityFile, created: bool, **kwargs):
    # spouštět jen při vytvoření nového souboru
    if not created:
        return

    # jen FIT
    if instance.file_type != ActivityFile.FileType.FIT:
        return

    activity = instance.activity

    # MVP (zatím bez parseru):
    # - při uploadu FIT vždy smažeme staré intervaly, aby se neduplikovaly indexy
    # - později sem doplníme parser, který je znovu vytvoří
    with transaction.atomic():
        ActivityInterval.objects.filter(activity=activity).delete()

    # TODO: tady později zavoláme parser a z FITu vytvoříme intervaly + agregáty
