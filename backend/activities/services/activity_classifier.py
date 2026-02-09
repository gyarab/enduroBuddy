from __future__ import annotations

from typing import List, Dict, Any

from activities.models import Activity


def classify_activity(activity: Activity, intervals: List[Dict[str, Any]]) -> str:
    """
    Vrací jednu z:
      Activity.WorkoutType.RUN
      Activity.WorkoutType.WORKOUT
      Activity.WorkoutType.UNKNOWN
    """
    # MVP pravidlo (příklad): když je hodně různých délek lapů → workout
    dists = [i.get("distance_m") for i in intervals if i.get("distance_m")]
    if len(dists) < 3:
        return Activity.WorkoutType.UNKNOWN

    # jestli je velká variabilita vzdáleností, je to spíš workout
    mn, mx = min(dists), max(dists)
    if mx - mn > 200:  # laditelné
        return Activity.WorkoutType.WORKOUT

    return Activity.WorkoutType.RUN
