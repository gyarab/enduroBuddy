from __future__ import annotations

from typing import Any, Dict, List, Optional

from datetime import datetime


def _safe_int(x) -> Optional[int]:
    try:
        if x is None:
            return None
        return int(round(float(x)))
    except Exception:
        return None


def _pace_s_per_km(distance_m: Optional[int], duration_s: Optional[int]) -> Optional[int]:
    if not distance_m or not duration_s:
        return None
    if distance_m < 50:
        return None
    # pace = seconds / km
    km = distance_m / 1000.0
    return _safe_int(duration_s / km)


def parse_fit_file(path: str) -> Dict[str, Any]:
    """
    Returns:
      {
        "activity": {...},
        "intervals": [...]
      }
    """
    try:
        from fitparse import FitFile
    except ImportError as e:
        raise ImportError("Missing dependency: fitparse. Run: pip install fitparse") from e

    fit = FitFile(path)

    # --------- Aggregates from SESSION ----------
    activity_data: Dict[str, Any] = {}
    started_at: Optional[datetime] = None
    total_distance_m: Optional[int] = None
    total_timer_s: Optional[int] = None
    avg_hr: Optional[int] = None

    # fitparse field names are usually: start_time, total_distance, total_timer_time, avg_heart_rate
    for msg in fit.get_messages("session"):
        fields = {f.name: f.value for f in msg}
        started_at = fields.get("start_time") or started_at
        total_distance_m = _safe_int(fields.get("total_distance")) or total_distance_m
        total_timer_s = _safe_int(fields.get("total_timer_time")) or total_timer_s
        avg_hr = _safe_int(fields.get("avg_heart_rate")) or avg_hr

    avg_pace = _pace_s_per_km(total_distance_m, total_timer_s)

    activity_data.update({
        "started_at": started_at,
        "distance_m": total_distance_m,
        "duration_s": total_timer_s,
        "avg_hr": avg_hr,
        "avg_pace_s_per_km": avg_pace,
    })

    # --------- Intervals from LAP ----------
    intervals: List[Dict[str, Any]] = []

    for msg in fit.get_messages("lap"):
        fields = {f.name: f.value for f in msg}

        lap_distance = _safe_int(fields.get("total_distance"))
        lap_time = _safe_int(fields.get("total_timer_time")) or _safe_int(fields.get("total_elapsed_time"))
        lap_avg_hr = _safe_int(fields.get("avg_heart_rate"))
        lap_avg_pace = _pace_s_per_km(lap_distance, lap_time)

        # vyfiltrujeme nulové / divné lapy
        if not lap_time and not lap_distance:
            continue
        if lap_distance is not None and lap_distance < 30:
            continue

        intervals.append({
            "duration_s": lap_time,
            "distance_m": lap_distance,
            "avg_hr": lap_avg_hr,
            "avg_pace_s_per_km": lap_avg_pace,
            "note": "",
        })

    return {
        "activity": activity_data,
        "intervals": intervals,
    }
