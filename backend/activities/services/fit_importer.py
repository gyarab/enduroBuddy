from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import BinaryIO, Optional

from django.db import transaction
from django.utils import timezone

from activities.models import Activity, ActivityFile, ActivityInterval, ActivitySample
from activities.services.fit_parser import parse_fit_file


@dataclass(frozen=True)
class FitImportOutcome:
    activity: Activity
    intervals_created: int
    samples_created: int


def import_fit_into_activity(
    *,
    activity: Activity,
    fileobj: BinaryIO,
    original_name: str | None = None,
    create_activity_file_row: bool = True,
) -> FitImportOutcome:
    """
    Rozparsuje FIT a uloží data do DB.
    Soubor se nikam neukládá (parsujeme z fileobj).
    Vrací FitImportOutcome kvůli testům a diagnostice.
    """

    # parse mimo transakci (rychlé a bez locků)
    res = parse_fit_file(fileobj)
    s = res.summary or {}

    started_at = s.get("started_at")
    if isinstance(started_at, datetime) and timezone.is_naive(started_at):
        started_at = timezone.make_aware(started_at, timezone.get_current_timezone())

    with transaction.atomic():
        # volitelný "log" záznam (bez file)
        if create_activity_file_row:
            ActivityFile.objects.create(
                activity=activity,
                file_type=ActivityFile.FileType.FIT,
                file=None,
                original_name=original_name or "",
            )

        # update Activity summary
        activity.started_at = started_at or activity.started_at
        activity.title = s.get("title") or activity.title
        activity.sport = s.get("sport") or activity.sport
        activity.workout_type = s.get("workout_type") or activity.workout_type

        activity.duration_s = s.get("duration_s")
        activity.distance_m = s.get("distance_m")
        activity.avg_hr = s.get("avg_hr")
        activity.max_hr = s.get("max_hr")
        activity.avg_pace_s_per_km = s.get("avg_pace_s_per_km")
        activity.save()

        # intervals
        ActivityInterval.objects.filter(activity=activity).delete()
        intervals = [
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
            for i, row in enumerate(res.intervals or [], start=1)
        ]
        if intervals:
            ActivityInterval.objects.bulk_create(intervals, batch_size=500)

        # samples
        ActivitySample.objects.filter(activity=activity).delete()
        samples = [
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
            for row in (res.samples or [])
        ]
        if samples:
            ActivitySample.objects.bulk_create(samples, batch_size=2000)

    return FitImportOutcome(
        activity=activity,
        intervals_created=len(intervals),
        samples_created=len(samples),
    )
