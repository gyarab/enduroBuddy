from __future__ import annotations

from datetime import datetime

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import ActivityFile, ActivityInterval, ActivitySample
from .services.fit_parser import parse_fit_file


@receiver(post_save, sender=ActivityFile)
def parse_fit_on_upload(sender, instance: ActivityFile, created: bool, **kwargs):
    # pouze při vytvoření souboru
    if not created:
        return

    if instance.file_type != ActivityFile.FileType.FIT:
        return

    if not instance.file:
        return

    activity = instance.activity

    # 1) Parse mimo DB transakci (rychlejší + žádné locky)
    #    - použij file.path (když existuje) nebo file.file (in-memory upload)
    source = instance.file.path if getattr(instance.file, "path", None) else instance.file.file
    res = parse_fit_file(source)
    s = res.summary or {}

    # timezone-safe started_at
    started_at = s.get("started_at")
    if isinstance(started_at, datetime) and timezone.is_naive(started_at):
        started_at = timezone.make_aware(started_at, timezone.get_current_timezone())

    # 2) DB změny v jedné transakci
    with transaction.atomic():
        wt = s.get("workout_type") or activity.workout_type

        activity.started_at = started_at or activity.started_at
        activity.title = s.get("title") or activity.title
        activity.sport = s.get("sport") or activity.sport
        activity.workout_type = wt

        activity.duration_s = s.get("duration_s")
        activity.distance_m = s.get("distance_m")

        # avg_hr: u workoutu použij work_avg_hr (bez pauz), fallback na session avg_hr
        if wt == "WORKOUT":
            activity.avg_hr = s.get("work_avg_hr") or s.get("avg_hr")
        else:
            activity.avg_hr = s.get("avg_hr")

        activity.max_hr = s.get("max_hr")
        activity.avg_pace_s_per_km = s.get("avg_pace_s_per_km")

        activity.save()

        # přegeneruj intervaly
        ActivityInterval.objects.filter(activity=activity).delete()

        intervals = []
        for i, row in enumerate(res.intervals or [], start=1):
            intervals.append(
                ActivityInterval(
                    activity=activity,
                    index=i,
                    duration_s=row.get("duration_s"),
                    distance_m=row.get("distance_m"),
                    avg_hr=row.get("avg_hr"),
                    max_hr=row.get("max_hr"),
                    avg_pace_s_per_km=row.get("avg_pace_s_per_km"),
                    note=row.get("note") or "",
                )
            )
        if intervals:
            ActivityInterval.objects.bulk_create(intervals, batch_size=500)

        # přegeneruj samples (time-series, bez GPS)
        ActivitySample.objects.filter(activity=activity).delete()

        samples = []
        for row in res.samples or []:
            samples.append(
                ActivitySample(
                    activity=activity,
                    t_s=row.get("t_s"),
                    distance_m=row.get("distance_m"),
                    hr=row.get("hr"),
                    speed_m_s=row.get("speed_m_s"),
                    cadence=row.get("cadence"),
                    power=row.get("power"),
                    altitude_m=row.get("altitude_m"),
                )
            )
        if samples:
            ActivitySample.objects.bulk_create(samples, batch_size=2000)

    # 3) smaž FIT soubor z disku po úspěšném importu (ať ti nezůstává media/)
    #    - necháme řádek v DB (ActivityFile), ale bez fyzického souboru
    try:
        instance.file.delete(save=False)
    except Exception:
        # nechceme shodit import, kdyby delete selhal (Windows lock apod.)
        pass
