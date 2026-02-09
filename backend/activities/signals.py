from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import ActivityFile, ActivityInterval, ActivityLap, ActivityRecord
from .services.fit_parser import parse_fit_file
from .services.activity_classifier import classify_activity


def _median(values: List[int]) -> Optional[float]:
    if not values:
        return None
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return float(s[mid])
    return (s[mid - 1] + s[mid]) / 2.0


def select_work_intervals_from_laps(laps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Heuristika pro WORKOUT:
    - vybereme jen pracovní intervaly (bez pauz)
    - pauzy typicky vyjdou výrazně pomalejší než pracovní úseky

    Pravidlo (MVP):
    - spočítáme median pace z lapů, které pace mají
    - work interval = pace <= median * 0.85  (>= ~15 % rychlejší než median)
    - ještě filtr: duration >= 20s a distance >= 80m (abychom vyhodili šum)
    """
    paces = [l.get("avg_pace_s_per_km") for l in laps if l.get("avg_pace_s_per_km")]
    paces_int = [p for p in paces if isinstance(p, int) and p > 0]
    med = _median(paces_int)

    out: List[Dict[str, Any]] = []

    for l in laps:
        dur = l.get("duration_s")
        dist = l.get("distance_m")
        pace = l.get("avg_pace_s_per_km")

        if dur is not None and dur < 20:
            continue
        if dist is not None and dist < 80:
            continue

        if med is None:
            # fallback: když nemáme pace, nefiltrujeme (radši něco než nic)
            out.append(l)
            continue

        if pace is None:
            continue

        # work = rychlejší než median
        if pace <= med * 0.85:
            out.append(l)

    return out


@receiver(post_save, sender=ActivityFile)
def parse_fit_on_upload(sender, instance: ActivityFile, created: bool, **kwargs):
    # nic nedělej pokud soubor už neexistuje (třeba jsme ho po importu smazali)
    if not instance.file:
        return

    # jen FIT v tomhle MVP
    if instance.file_type != ActivityFile.FileType.FIT:
        return

    activity = instance.activity

    parsed = parse_fit_file(instance.file.path)

    activity_data = parsed.get("activity") or {}
    laps = parsed.get("laps") or []
    records = parsed.get("records") or []

    # vše uděláme v transakci, ať to je konzistentní
    with transaction.atomic():
        # ulož agregace do Activity
        activity.started_at = activity_data.get("started_at") or activity.started_at
        activity.distance_m = activity_data.get("distance_m") or activity.distance_m
        activity.duration_s = activity_data.get("duration_s") or activity.duration_s
        activity.avg_hr = activity_data.get("avg_hr") or activity.avg_hr
        activity.max_hr = activity_data.get("max_hr") or activity.max_hr
        activity.avg_pace_s_per_km = activity_data.get("avg_pace_s_per_km") or activity.avg_pace_s_per_km

        # klasifikace typu aktivity (RUN vs WORKOUT vs UNKNOWN)
        # NOTE: classifier necháváme na tobě – teď mu posíláme lapy (dřív to byly “intervals”)
        activity.workout_type = classify_activity(activity, laps)
        activity.save()

        # ===== Uložit LAPY (raw) =====
        ActivityLap.objects.filter(activity=activity).delete()
        lap_objs = []
        for i, l in enumerate(laps, start=1):
            lap_objs.append(
                ActivityLap(
                    activity=activity,
                    index=i,
                    duration_s=l.get("duration_s"),
                    distance_m=l.get("distance_m"),
                    avg_hr=l.get("avg_hr"),
                    max_hr=l.get("max_hr"),
                    avg_pace_s_per_km=l.get("avg_pace_s_per_km"),
                )
            )
        if lap_objs:
            ActivityLap.objects.bulk_create(lap_objs)

        # ===== Uložit RECORDS (time-series) =====
        ActivityRecord.objects.filter(activity=activity).delete()
        rec_objs = []
        for r in records:
            rec_objs.append(
                ActivityRecord(
                    activity=activity,
                    ts=r.get("ts"),
                    distance_m=r.get("distance_m"),
                    speed_mps=r.get("speed_mps"),
                    hr=r.get("hr"),
                    cadence=r.get("cadence"),
                    altitude_m=r.get("altitude_m"),
                    lat=r.get("lat"),
                    lon=r.get("lon"),
                )
            )
        if rec_objs:
            ActivityRecord.objects.bulk_create(rec_objs)

        # ===== Uložit DASHBOARD "INTERVALY" =====
        # - RUN: intervaly nechceme (proto smažeme a nic nevložíme)
        # - WORKOUT: uložíme jen work intervals (bez pauz)
        ActivityInterval.objects.filter(activity=activity).delete()

        if activity.workout_type == activity.WorkoutType.WORKOUT:
            work_laps = select_work_intervals_from_laps(laps)

            int_objs = []
            for i, it in enumerate(work_laps, start=1):
                int_objs.append(
                    ActivityInterval(
                        activity=activity,
                        index=i,
                        duration_s=it.get("duration_s"),
                        distance_m=it.get("distance_m"),
                        avg_hr=it.get("avg_hr"),
                        max_hr=it.get("max_hr"),
                        avg_pace_s_per_km=it.get("avg_pace_s_per_km"),
                        note="",
                    )
                )
            if int_objs:
                ActivityInterval.objects.bulk_create(int_objs)

        # ===== uložit raw JSON (malé debug info) =====
        # ===== uložit raw JSON (malé debug info) =====
            instance.raw_json = json_safe(parsed)
            instance.save(update_fields=["raw_json"])


        # soubor zahodíme (nebude se hromadit v Dockeru)
        instance.file.delete(save=False)
        instance.file = None
        instance.save(update_fields=["file"])

def json_safe(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_safe(v) for v in obj]
    return obj
