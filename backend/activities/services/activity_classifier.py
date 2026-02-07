from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Iterable, Optional

from activities.models import Activity


@dataclass
class IntervalFeatures:
    count: int
    mean_dist_m: float
    dist_cv: float
    mean_pace: Optional[float]
    pace_cv: Optional[float]
    has_alt_work_rest: bool
    looks_like_auto_laps_1km: bool


def _safe_cv(values: list[float]) -> float:
    """
    Coefficient of variation (std/mean), safe for small/zero.
    """
    if not values:
        return 0.0
    m = mean(values)
    if m <= 0:
        return 0.0
    return pstdev(values) / m


def _extract_features(intervals: Iterable, *, dist_tol_m: int = 80) -> IntervalFeatures:
    """
    intervals = queryset/list of ActivityInterval
    """
    ints = list(intervals)
    dists = [i.distance_m for i in ints if i.distance_m]
    paces = [i.avg_pace_s_per_km for i in ints if i.avg_pace_s_per_km]

    mean_dist = float(mean(dists)) if dists else 0.0
    dist_cv = _safe_cv([float(x) for x in dists])

    mean_pace = float(mean(paces)) if paces else None
    pace_cv = _safe_cv([float(x) for x in paces]) if paces else None

    # Detekce auto-laps ~1km (Garmin často dává intervaly po 1 km i u "easy run")
    looks_like_1km = False
    if dists and len(dists) >= 5:
        close_to_1km = sum(1 for d in dists if abs(d - 1000) <= dist_tol_m)
        # pokud většina intervalů ~1000m -> auto-laps
        looks_like_1km = (close_to_1km / len(dists)) >= 0.7

    # Detekce střídání práce/odpočinku:
    # jednoduché: pace se "houpe" (rychle/pomalu/rychle/pomalu) nebo distance střídá krátké/dlouhé.
    has_alt = False
    if paces and len(paces) >= 6:
        # rozdíly mezi sousedy
        diffs = [abs(paces[i] - paces[i - 1]) for i in range(1, len(paces))]
        # pokud je hodně velkých skoků, typicky to značí intervaly
        has_alt = (sum(1 for d in diffs if d >= 25) / len(diffs)) >= 0.5  # 25 s/km je už citelná změna
    elif dists and len(dists) >= 6:
        diffs = [abs(dists[i] - dists[i - 1]) for i in range(1, len(dists))]
        has_alt = (sum(1 for d in diffs if d >= 250) / len(diffs)) >= 0.5  # 250 m skok

    return IntervalFeatures(
        count=len(ints),
        mean_dist_m=mean_dist,
        dist_cv=float(dist_cv),
        mean_pace=mean_pace,
        pace_cv=float(pace_cv) if pace_cv is not None else None,
        has_alt_work_rest=has_alt,
        looks_like_auto_laps_1km=looks_like_1km,
    )


def classify_activity_workout_type(activity: Activity) -> str:
    """
    Returns one of Activity.WorkoutType.*
    """
    intervals = list(activity.intervals.all())

    # když žádné intervaly, zkus spadnout na UNKNOWN/EASY podle agregátů
    if len(intervals) == 0:
        # pokud má distance a duration, je to aspoň "nějaký běh"
        if activity.distance_m and activity.duration_s:
            return Activity.WorkoutType.EASY
        return Activity.WorkoutType.UNKNOWN

    f = _extract_features(intervals)

    # Málo intervalů -> těžko poznat
    if f.count < 4:
        return Activity.WorkoutType.UNKNOWN

    # 1) Pokud to vypadá jako auto-laps 1 km a intervaly jsou hodně podobné -> EASY
    #    (cv distance malé a pace cv malé)
    if f.looks_like_auto_laps_1km:
        if f.dist_cv <= 0.08 and (f.pace_cv is None or f.pace_cv <= 0.06) and not f.has_alt_work_rest:
            return Activity.WorkoutType.EASY

    # 2) Pokud je patrné střídání work/rest -> WORKOUT
    if f.has_alt_work_rest:
        return Activity.WorkoutType.WORKOUT

    # 3) Pokud intervaly mají různou délku nebo tempo výrazně kolísá -> WORKOUT
    if f.dist_cv >= 0.18:
        return Activity.WorkoutType.WORKOUT
    if f.pace_cv is not None and f.pace_cv >= 0.10:
        return Activity.WorkoutType.WORKOUT

    # 4) Jinak default EASY
    return Activity.WorkoutType.EASY
