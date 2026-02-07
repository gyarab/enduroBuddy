from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fitparse import FitFile


@dataclass
class FitInterval:
    index: int
    duration_s: Optional[int] = None
    distance_m: Optional[int] = None
    avg_hr: Optional[int] = None
    avg_pace_s_per_km: Optional[int] = None


def _safe_int(x):
    try:
        return int(x) if x is not None else None
    except Exception:
        return None


def _pace_s_per_km_from_speed_mps(speed_mps: float | None) -> Optional[int]:
    # pace = 1000 / speed (sec/km)
    if not speed_mps:
        return None
    if speed_mps <= 0:
        return None
    return int(round(1000.0 / float(speed_mps)))


def parse_fit_file(path: str) -> dict:
    """
    Vrátí:
      - activity: agregáty (duration_s, distance_m, avg_hr, avg_pace_s_per_km, started_at)
      - intervals: list intervalů (laps)
    """
    fit = FitFile(path)

    # ---- activity summary (z "session") ----
    activity = {
        "started_at": None,
        "duration_s": None,
        "distance_m": None,
        "avg_hr": None,
        "avg_pace_s_per_km": None,
    }

    for msg in fit.get_messages("session"):
        fields = {f.name: f.value for f in msg}
        activity["started_at"] = fields.get("start_time") or activity["started_at"]
        activity["duration_s"] = _safe_int(fields.get("total_timer_time")) or activity["duration_s"]
        activity["distance_m"] = _safe_int(fields.get("total_distance")) or activity["distance_m"]
        activity["avg_hr"] = _safe_int(fields.get("avg_heart_rate")) or activity["avg_hr"]

        avg_speed = fields.get("avg_speed")  # m/s
        if activity["avg_pace_s_per_km"] is None:
            activity["avg_pace_s_per_km"] = _pace_s_per_km_from_speed_mps(avg_speed)

        break  # bereme první session

    # ---- intervals (z "lap") ----
    intervals: list[FitInterval] = []
    idx = 1
    for msg in fit.get_messages("lap"):
        fields = {f.name: f.value for f in msg}

        duration_s = _safe_int(fields.get("total_timer_time"))
        distance_m = _safe_int(fields.get("total_distance"))
        avg_hr = _safe_int(fields.get("avg_heart_rate"))
        avg_speed = fields.get("avg_speed")

        intervals.append(
            FitInterval(
                index=idx,
                duration_s=duration_s,
                distance_m=distance_m,
                avg_hr=avg_hr,
                avg_pace_s_per_km=_pace_s_per_km_from_speed_mps(avg_speed),
            )
        )
        idx += 1

    return {"activity": activity, "intervals": intervals}
