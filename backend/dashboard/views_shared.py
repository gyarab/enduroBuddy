from __future__ import annotations

import secrets
from datetime import timedelta

from django.utils import timezone

from accounts.models import CoachAthlete, Profile, Role, TrainingGroup, TrainingGroupAthlete, TrainingGroupInvite
from training.models import CompletedTraining, PlannedTraining

def _coach_accessible_athlete_ids(*, coach_user) -> set[int]:
    accessible_ids = set(
        CoachAthlete.objects.filter(coach=coach_user).values_list("athlete_id", flat=True)
    )
    group_member_ids = set(
        TrainingGroupAthlete.objects.filter(group__coach=coach_user).values_list("athlete_id", flat=True)
    )
    accessible_ids.update(group_member_ids)
    accessible_ids.add(coach_user.id)
    return accessible_ids


def _coach_can_access_athlete(*, coach_user, athlete_id: int, accessible_ids: set[int] | None = None) -> bool:
    if accessible_ids is not None:
        return athlete_id in accessible_ids
    if coach_user.id == athlete_id:
        return True
    has_direct_link = CoachAthlete.objects.filter(coach=coach_user, athlete_id=athlete_id).exists()
    has_group_link = TrainingGroupAthlete.objects.filter(group__coach=coach_user, athlete_id=athlete_id).exists()
    return bool(has_direct_link or has_group_link)


def _get_cached_coach_accessible_ids(request) -> set[int]:
    cache_key = "_coach_accessible_ids"
    cached = getattr(request, cache_key, None)
    if cached is None:
        cached = _coach_accessible_athlete_ids(coach_user=request.user)
        setattr(request, cache_key, cached)
    return cached


def _parse_optional_int(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        raw = value.strip()
        if raw in {"", "-"}:
            return None
        if raw.isdigit():
            return int(raw)
    raise ValueError("Invalid integer value.")


def _parse_optional_distance_m(value):
    if value is None:
        return None
    if isinstance(value, str):
        raw = value.strip().replace(",", ".")
        if raw in {"", "-"}:
            return None
        km = float(raw)
    elif isinstance(value, (int, float)):
        km = float(value)
    else:
        raise ValueError("Invalid km value.")
    if km < 0:
        raise ValueError("Invalid km value.")
    return int(round(km * 1000))


def _parse_optional_minutes_to_seconds(value):
    minutes = _parse_optional_int(value)
    if minutes is None:
        return None
    if minutes < 0:
        raise ValueError("Invalid minutes value.")
    return int(minutes) * 60


def _create_training_group_invite(*, group: TrainingGroup, created_by, invited_email: str = "") -> TrainingGroupInvite:
    token = secrets.token_urlsafe(32)
    return TrainingGroupInvite.objects.create(
        group=group,
        created_by=created_by,
        token=token,
        invited_email=invited_email.strip(),
        expires_at=timezone.now() + timedelta(days=7),
    )


def _resolve_coach_from_code(raw_code: str):
    normalized = (raw_code or "").strip().upper()
    if not normalized:
        return None
    profile = Profile.objects.select_related("user").filter(role=Role.COACH, coach_join_code=normalized).first()
    return profile.user if profile else None

def _update_completed_training_for_planned(*, planned: PlannedTraining, field: str, value):
    completed, _ = CompletedTraining.objects.get_or_create(planned=planned)

    def _set_and_save_if_changed(instance, updates: dict[str, object]) -> None:
        changed_fields = []
        for key, new_value in updates.items():
            if getattr(instance, key) != new_value:
                setattr(instance, key, new_value)
                changed_fields.append(key)
        if changed_fields:
            instance.save(update_fields=changed_fields)

    if field == "km":
        distance_m = _parse_optional_distance_m(value)
        _set_and_save_if_changed(completed, {"distance_m": distance_m})
        return "-" if completed.distance_m is None else f"{completed.distance_m / 1000.0:.2f}"

    if field == "min":
        time_seconds = _parse_optional_minutes_to_seconds(value)
        _set_and_save_if_changed(completed, {"time_seconds": time_seconds})
        if completed.time_seconds is None:
            return "-"
        return str(int(round(completed.time_seconds / 60.0)))

    if field == "third":
        if not isinstance(value, str):
            raise ValueError("Invalid text value.")
        _set_and_save_if_changed(completed, {"note": value})
        return value or "-"

    if field == "avg_hr":
        avg_hr = _parse_optional_int(value)
        if avg_hr is not None and avg_hr < 0:
            raise ValueError("Invalid avg_hr value.")
        _set_and_save_if_changed(completed, {"avg_hr": avg_hr})
        return completed.avg_hr

    if field == "max_hr":
        max_hr = _parse_optional_int(value)
        if max_hr is not None and max_hr < 0:
            raise ValueError("Invalid max_hr value.")
        feel = "" if max_hr is None else str(max_hr)
        _set_and_save_if_changed(completed, {"feel": feel})
        if getattr(planned, "activity", None):
            _set_and_save_if_changed(planned.activity, {"max_hr": max_hr})
        return max_hr

    raise ValueError("Invalid field.")


