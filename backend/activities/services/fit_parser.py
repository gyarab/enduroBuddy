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


def _safe_float(x) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _pace_s_per_km(distance_m: Optional[int], duration_s: Optional[int]) -> Optional[int]:
    if not distance_m or not duration_s:
        return None
    if distance_m < 50:
        return None
    km = distance_m / 1000.0
    return _safe_int(duration_s / km)


def _semicircles_to_deg(x) -> Optional[float]:
    # FIT position_lat/position_long jsou často v "semicircles"
    try:
        if x is None:
            return None
        return float(x) * (180.0 / 2**31)
    except Exception:
        return None


def parse_fit_file(path: str) -> Dict[str, Any]:
    """
    Vrací maximum užitečných dat:

    {
      "activity": {
        "started_at": datetime|None,
        "distance_m": int|None,
        "duration_s": int|None,
        "avg_hr": int|None,
        "max_hr": int|None,
        "avg_pace_s_per_km": int|None,
      },
      "laps": [
        {"duration_s":..., "distance_m":..., "avg_hr":..., "max_hr":..., "avg_pace_s_per_km":...},
        ...
      ],
      "records": [
        {"ts":..., "distance_m":..., "speed_mps":..., "hr":..., "cadence":..., "altitude_m":..., "lat":..., "lon":...},
        ...
      ],
      "raw": { ...malý debug výtah... }
    }
    """
    try:
        from fitparse import FitFile
    except ImportError as e:
        raise ImportError("Missing dependency: fitparse. Run: pip install fitparse") from e

    fit = FitFile(path)

    # --------- Aggregates from SESSION ----------
    started_at: Optional[datetime] = None
    total_distance_m: Optional[int] = None
    total_timer_s: Optional[int] = None
    avg_hr: Optional[int] = None
    max_hr: Optional[int] = None

    for msg in fit.get_messages("session"):
        fields = {f.name: f.value for f in msg}
        started_at = fields.get("start_time") or started_at
        total_distance_m = _safe_int(fields.get("total_distance")) or total_distance_m
        total_timer_s = _safe_int(fields.get("total_timer_time")) or total_timer_s
        avg_hr = _safe_int(fields.get("avg_heart_rate")) or avg_hr
        max_hr = _safe_int(fields.get("max_heart_rate")) or max_hr
        # bereme první session (většinou jedna)
        break

    avg_pace = _pace_s_per_km(total_distance_m, total_timer_s)

    activity_data: Dict[str, Any] = {
        "started_at": started_at,
        "distance_m": total_distance_m,
        "duration_s": total_timer_s,
        "avg_hr": avg_hr,
        "max_hr": max_hr,
        "avg_pace_s_per_km": avg_pace,
    }

    # --------- Laps from LAP ----------
    laps: List[Dict[str, Any]] = []
    for msg in fit.get_messages("lap"):
        fields = {f.name: f.value for f in msg}

        lap_distance = _safe_int(fields.get("total_distance"))
        lap_time = _safe_int(fields.get("total_timer_time")) or _safe_int(fields.get("total_elapsed_time"))

        lap_avg_hr = _safe_int(fields.get("avg_heart_rate"))
        lap_max_hr = _safe_int(fields.get("max_heart_rate"))

        lap_avg_pace = _pace_s_per_km(lap_distance, lap_time)

        if not lap_time and not lap_distance:
            continue
        if lap_distance is not None and lap_distance < 30:
            continue

        laps.append({
            "duration_s": lap_time,
            "distance_m": lap_distance,
            "avg_hr": lap_avg_hr,
            "max_hr": lap_max_hr,
            "avg_pace_s_per_km": lap_avg_pace,
        })

    # --------- Records from RECORD ----------
    records: List[Dict[str, Any]] = []
    # max_hr fallback: když session max_hr není, dopočítáme z recordů
    record_max_hr: Optional[int] = None

    for msg in fit.get_messages("record"):
        fields = {f.name: f.value for f in msg}

        ts = fields.get("timestamp")
        dist = _safe_int(fields.get("distance"))
        speed = _safe_float(fields.get("speed"))
        hr = _safe_int(fields.get("heart_rate"))
        cad = _safe_int(fields.get("cadence"))
        alt = _safe_float(fields.get("altitude"))

        lat = _semicircles_to_deg(fields.get("position_lat"))
        lon = _semicircles_to_deg(fields.get("position_long"))

        if hr is not None:
            record_max_hr = max(record_max_hr or hr, hr)

        # filtr: pokud není nic, nemá smysl ukládat
        if ts is None and dist is None and speed is None and hr is None and cad is None and alt is None and lat is None and lon is None:
            continue

        records.append({
            "ts": ts,
            "distance_m": dist,
            "speed_mps": speed,
            "hr": hr,
            "cadence": cad,
            "altitude_m": alt,
            "lat": lat,
            "lon": lon,
        })

    # max_hr fallback
    if activity_data.get("max_hr") is None and record_max_hr is not None:
        activity_data["max_hr"] = record_max_hr

    raw_small = {
        "has_session": started_at is not None,
        "lap_count": len(laps),
        "record_count": len(records),
    }

    return {
        "activity": activity_data,
        "laps": laps,
        "records": records,
        "raw": raw_small,
    }
