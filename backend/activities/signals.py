from __future__ import annotations

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import ActivityFile, ActivityInterval
from .services.fit_parser import parse_fit_file
from .services.activity_classifier import classify_activity_workout_type


@receiver(post_save, sender=ActivityFile)
def parse_fit_on_upload(sender, instance: ActivityFile, created: bool, **kwargs):
    """
    Po uploadu FIT souboru:
    - naparsuje data
    - uloží agregáty do Activity
    - vytvoří ActivityIntervaly
    - klasifikuje workout_type (EASY/WORKOUT/UNKNOWN)
    """

    # spouštíme jen při vytvoření a jen pro FIT
    if not created:
        return
    if instance.file_type != ActivityFile.FileType.FIT:
        return
    if not instance.file:
        return

    activity = instance.activity
    file_path = instance.file.path

    parsed = parse_fit_file(file_path)
    activity_data = parsed.get("activity", {}) or {}
    intervals_data = parsed.get("intervals", []) or []

    with transaction.atomic():
        # ===== uložit agregáty do Activity =====
        started_at = activity_data.get("started_at")
        if started_at:
            # fitparse často vrací naive datetime -> uděláme aware podle TIME_ZONE
            if timezone.is_naive(started_at):
                started_at = timezone.make_aware(started_at, timezone.get_current_timezone())
            activity.started_at = started_at

        # tyhle hodnoty se uloží jen když existují v dictu
        for field in ("duration_s", "distance_m", "avg_hr", "avg_pace_s_per_km", "title"):
            if field in activity_data:
                setattr(activity, field, activity_data.get(field))

        activity.save()

        # ===== přegenerovat intervaly (aby nepadal UNIQUE(activity, index)) =====
        activity.intervals.all().delete()

        for idx, it in enumerate(intervals_data, start=1):
            ActivityInterval.objects.create(
                activity=activity,
                index=idx,
                duration_s=it.get("duration_s"),
                distance_m=it.get("distance_m"),
                avg_hr=it.get("avg_hr"),
                avg_pace_s_per_km=it.get("avg_pace_s_per_km"),
                note=it.get("note", ""),
            )

        # ===== klasifikace workout_type (po vytvoření intervalů) =====
        activity.workout_type = classify_activity_workout_type(activity)
        activity.save(update_fields=["workout_type"])
