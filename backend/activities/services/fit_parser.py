from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

# pip: fitparse
from fitparse import FitFile


@dataclass
class FitParseResult:
    summary: dict[str, Any]
    intervals: list[dict[str, Any]]


def _val(msg, field: str):
    try:
        return msg.get_value(field)
    except Exception:
        return None



def _secs(td):
    if td is None:
        return None
    # fitparse někdy vrací timedelta, někdy číslo
    try:
        return int(td.total_seconds())
    except Exception:
        try:
            return int(td)
        except Exception:
            return None


def parse_fit_file(path: str) -> FitParseResult:
    fit = FitFile(path)
    fit.parse()

    session = None
    sport = None
    sub_sport = None
    started_at = None
    total_time_s = None
    total_dist_m = None
    avg_hr = None
    avg_speed = None  # m/s

    # 1) SESSION summary
    for msg in fit.get_messages("session"):
        session = msg
        sport = _val(msg, "sport")
        sub_sport = _val(msg, "sub_sport")
        started_at = _val(msg, "start_time")
        total_time_s = _secs(_val(msg, "total_timer_time"))
        total_dist_m = _val(msg, "total_distance")
        avg_hr = _val(msg, "avg_heart_rate")
        avg_speed = _val(msg, "avg_speed")
        break

    # 2) Detect workout steps (structured workouts)
    has_workout_steps = False
    for _ in fit.get_messages("workout_step"):
        has_workout_steps = True
        break

    # 3) Intervals from LAPs (nejčastější a nejspolehlivější)
    laps = []
    for lap in fit.get_messages("lap"):
        lap_time = _secs(_val(lap, "total_timer_time"))
        lap_dist = _val(lap, "total_distance")
        lap_avg_hr = _val(lap, "avg_heart_rate")
        lap_avg_speed = _val(lap, "avg_speed")

        if lap_time is None and lap_dist is None:
            continue

        pace_s_per_km = None
        # pace: buď z avg_speed, nebo z time/dist
        if lap_avg_speed and lap_avg_speed > 0:
            pace_s_per_km = int(round(1000.0 / float(lap_avg_speed)))
        elif lap_time is not None and lap_dist and lap_dist > 0:
            pace_s_per_km = int(round(float(lap_time) / (float(lap_dist) / 1000.0)))

        laps.append(
            {
                "duration_s": lap_time,
                "distance_m": int(lap_dist) if lap_dist is not None else None,
                "avg_hr": int(lap_avg_hr) if lap_avg_hr is not None else None,
                "avg_pace_s_per_km": pace_s_per_km,
                "note": "",
            }
        )

    # 4) Fallback splits z RECORDů (např. 1km splits), když nejsou laps
    intervals = laps
    if not intervals:
        records = []
        for rec in fit.get_messages("record"):
            t = _val(rec, "timestamp")
            d = _val(rec, "distance")  # m (kumulativně)
            hr = _val(rec, "heart_rate")
            if t is None or d is None:
                continue
            records.append((t, float(d), int(hr) if hr is not None else None))

        # vytvoř 1km splits
        if records:
            km = 1
            start_i = 0
            while True:
                target = km * 1000.0
                end_i = None
                for i in range(start_i, len(records)):
                    if records[i][1] >= target:
                        end_i = i
                        break
                if end_i is None:
                    break

                t0, d0, _ = records[start_i]
                t1, d1, _ = records[end_i]

                dur = _secs(t1 - t0) if hasattr(t1, "__sub__") else None
                dist = d1 - d0
                if dist <= 0:
                    start_i = end_i
                    km += 1
                    continue

                pace = int(round(dur / (dist / 1000.0))) if dur is not None else None

                # avg hr v okně
                hrs = [h for (_, _, h) in records[start_i:end_i + 1] if h is not None]
                ahr = int(round(sum(hrs) / len(hrs))) if hrs else None

                intervals.append(
                    {
                        "duration_s": dur,
                        "distance_m": int(round(dist)),
                        "avg_hr": ahr,
                        "avg_pace_s_per_km": pace,
                        "note": f"{km} km",
                    }
                )

                start_i = end_i
                km += 1

    # 5) workout_type heuristic
    # - structured workout_step → workout
    # - víc lapů → workout
    # - jinak run
    workout_type = "workout" if (has_workout_steps or len(laps) >= 2) else "run"

    # 6) pace summary (z avg_speed, nebo z time/dist)
    avg_pace_s_per_km = None
    if avg_speed and float(avg_speed) > 0:
        avg_pace_s_per_km = int(round(1000.0 / float(avg_speed)))
    elif total_time_s is not None and total_dist_m and float(total_dist_m) > 0:
        avg_pace_s_per_km = int(round(float(total_time_s) / (float(total_dist_m) / 1000.0)))

    summary = {
        "started_at": started_at if isinstance(started_at, datetime) else None,
        "title": None,
        "sport": str(sport) if sport is not None else None,
        "workout_type": workout_type,
        "duration_s": int(total_time_s) if total_time_s is not None else None,
        "distance_m": int(total_dist_m) if total_dist_m is not None else None,
        "avg_hr": int(avg_hr) if avg_hr is not None else None,
        "avg_pace_s_per_km": avg_pace_s_per_km,
    }

    return FitParseResult(summary=summary, intervals=intervals)
