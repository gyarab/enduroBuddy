from __future__ import annotations

import secrets
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from accounts.models import CoachAthlete, Profile, Role, TrainingGroup, TrainingGroupAthlete, TrainingGroupInvite
from accounts.models import AppNotification
from accounts.services.notifications import upsert_app_notification
from activities.models import Activity
from training.models import CompletedTraining, PlannedTraining


_LEGEND_ZONE_KEYS = {"1", "2", "3", "4", "5"}
_LEGEND_DISTANCE_VALUES = {
    "800m",
    "1000m",
    "1 mile",
    "1500m",
    "2 miles",
    "3000m",
    "3k",
    "5000m",
    "5k",
    "10000m",
    "10k",
    "half marathon",
    "půlmaraton",
    "marathon",
    "maraton",
}

_TEST_NOTIFICATION_TEXTS = (
    ("success", "Test: Nový tréninkový plán je připraven."),
    ("info", "Test: Garmin synchronizace bude spuštěna za chvíli."),
    ("warning", "Test: Chybí ti vyplněný komentář u dnešního tréninku."),
    ("error", "Test: Nepodařilo se načíst jednu aktivitu."),
)

_TEST_CLIENT_NOTIFICATION_SCENARIOS = [
    {
        "delay_ms": 0,
        "action": "add",
        "id": "test-client-secondary",
        "text": "Test client: Tip v notifikačním baru.",
        "tone": "secondary",
        "unread": True,
        "persistent": False,
    },
    {
        "delay_ms": 120,
        "action": "add",
        "id": "test-client-warning",
        "text": "Test client: Garmin synchronizace běží.",
        "tone": "warning",
        "unread": True,
        "persistent": True,
        "statusLabel": "Running",
        "progressPercent": 24,
    },
    {
        "delay_ms": 900,
        "action": "update",
        "id": "test-client-warning",
        "text": "Test client: Garmin synchronizace dokončena.",
        "tone": "success",
        "persistent": False,
        "statusLabel": "Done",
        "progressPercent": 100,
    },
    {
        "delay_ms": 260,
        "action": "add",
        "id": "test-client-danger",
        "text": "Test client: Uložení tréninku selhalo.",
        "tone": "danger",
        "unread": True,
        "persistent": False,
    },
    {
        "delay_ms": 420,
        "action": "add",
        "id": "test-client-success",
        "text": "Test client: Druhá fáze byla přidána.",
        "tone": "success",
        "unread": True,
        "persistent": False,
    },
]


def sanitize_legend_state(raw_state: Any) -> dict[str, Any]:
    state = raw_state if isinstance(raw_state, dict) else {}
    cleaned: dict[str, Any] = {}

    raw_zones = state.get("zones")
    if isinstance(raw_zones, dict):
        zones: dict[str, dict[str, str]] = {}
        for key, value in raw_zones.items():
            zone_key = str(key).strip()
            if zone_key not in _LEGEND_ZONE_KEYS or not isinstance(value, dict):
                continue
            zone_from = str(value.get("from", "")).strip()[:3]
            zone_to = str(value.get("to", "")).strip()[:3]
            if zone_from and zone_to and zone_from.isdigit() and zone_to.isdigit():
                zones[zone_key] = {"from": zone_from, "to": zone_to}
        if zones:
            cleaned["zones"] = zones

    aerobic = str(state.get("aerobic_threshold", "")).strip()[:3]
    anaerobic = str(state.get("anaerobic_threshold", "")).strip()[:3]
    if aerobic.isdigit():
        cleaned["aerobic_threshold"] = aerobic
    if anaerobic.isdigit():
        cleaned["anaerobic_threshold"] = anaerobic

    raw_prs = state.get("prs")
    if isinstance(raw_prs, list):
        seen_distances = set()
        prs = []
        for item in raw_prs:
            if not isinstance(item, dict):
                continue
            distance = str(item.get("distance", "")).strip()
            if not distance:
                continue
            distance_key = distance.lower()
            if distance_key not in _LEGEND_DISTANCE_VALUES or distance_key in seen_distances:
                continue
            seen_distances.add(distance_key)
            prs.append(
                {
                    "distance": distance[:40],
                    "time": str(item.get("time", "")).strip()[:20],
                }
            )
        if prs:
            cleaned["prs"] = prs

    return cleaned


def maybe_add_test_notifications(request) -> None:
    setattr(request, "eb_include_test_app_notifications", False)
    if not settings.DEBUG:
        return
    raw_toggle = (request.GET.get("test_notifications") or "").strip().lower()
    if raw_toggle not in {"1", "true", "yes", "on", "all", "full"}:
        return

    for level, text in _TEST_NOTIFICATION_TEXTS:
        getattr(messages, level)(request, text)
    if raw_toggle in {"all", "full"}:
        setattr(request, "eb_include_test_app_notifications", True)
        if getattr(request.user, "is_authenticated", False):
            upsert_app_notification(
                recipient=request.user,
                kind=AppNotification.Kind.COACH_JOIN_REQUEST,
                tone=AppNotification.Tone.INFO,
                text="Test live: Nová žádost o trénování čeká na schválení.",
                dedupe_key=f"test-live-join-request:{request.user.id}",
            )
            upsert_app_notification(
                recipient=request.user,
                kind=AppNotification.Kind.PLAN_UPDATED,
                tone=AppNotification.Tone.INFO,
                text="Test live: Trenér přidal nový plán na zítřek.",
                dedupe_key=f"test-live-plan-updated:{request.user.id}",
            )
            upsert_app_notification(
                recipient=request.user,
                kind=AppNotification.Kind.COACH_NOTE,
                tone=AppNotification.Tone.INFO,
                text="Test live: Trenér přidal poznámku k tréninku.",
                dedupe_key=f"test-live-coach-note:{request.user.id}",
            )
        setattr(request, "eb_test_client_notifications", list(_TEST_CLIENT_NOTIFICATION_SCENARIOS))


def maybe_add_new_coach_request_notifications(request, pending_join_requests) -> None:
    if not getattr(request.user, "is_authenticated", False):
        return
    session_key = f"eb_seen_coach_join_request_ids_{request.user.id}"
    seen_ids = request.session.get(session_key, [])
    if not isinstance(seen_ids, list):
        seen_ids = []

    current_pending_ids = [int(req.id) for req in pending_join_requests if getattr(req, "id", None)]
    unseen_requests = [req for req in pending_join_requests if req.id not in seen_ids]
    if not unseen_requests:
        request.session[session_key] = current_pending_ids
        return

    if len(unseen_requests) == 1:
        request_text = f"Nova zadost o trenovani od {unseen_requests[0].athlete.username}."
    else:
        request_text = f"Mas {len(unseen_requests)} nove zadosti o trenovani."
    messages.info(request, request_text)
    request.session[session_key] = current_pending_ids

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


def _create_second_phase_for_planned(*, planned: PlannedTraining) -> PlannedTraining:
    if planned.date is None:
        raise ValueError("Cannot create a second phase for undated training.")

    with transaction.atomic():
        day_items = list(
            PlannedTraining.objects.select_for_update()
            .filter(week=planned.week, date=planned.date)
            .order_by("order_in_day", "id")
        )
        if not day_items:
            raise ValueError("Planned training day not found.")
        if len(day_items) > 1:
            raise ValueError("Second phase already exists for this day.")

        source = day_items[0]
        if source.is_two_phase_day:
            raise ValueError("Second phase already exists for this day.")

        source.is_two_phase_day = True
        source.save(update_fields=["is_two_phase_day"])

        return PlannedTraining.objects.create(
            week=source.week,
            date=source.date,
            day_label=source.day_label,
            title="",
            session_type=source.session_type,
            notes="",
            order_in_day=int(source.order_in_day) + 1,
            is_two_phase_day=True,
        )


def _remove_second_phase_for_planned(*, planned: PlannedTraining) -> int:
    if planned.date is None:
        raise ValueError("Cannot remove a second phase for undated training.")

    with transaction.atomic():
        day_items = list(
            PlannedTraining.objects.select_for_update()
            .filter(week=planned.week, date=planned.date)
            .order_by("order_in_day", "id")
        )
        if len(day_items) < 2:
            raise ValueError("Second phase does not exist for this day.")

        removed = day_items[-1]
        remaining = day_items[:-1]
        removed_id = removed.id
        removed.delete()

        if len(remaining) == 1:
            first = remaining[0]
            changed_fields = []
            if first.is_two_phase_day:
                first.is_two_phase_day = False
                changed_fields.append("is_two_phase_day")
            if first.order_in_day != 1:
                first.order_in_day = 1
                changed_fields.append("order_in_day")
            if changed_fields:
                first.save(update_fields=changed_fields)

        return removed_id

def _update_completed_training_for_planned(*, planned: PlannedTraining, field: str, value):
    completed, _ = CompletedTraining.objects.get_or_create(planned=planned)

    def _cleanup_completed_if_empty(instance: CompletedTraining) -> None:
        # An emptied completed row should disappear from both DB and dashboard.
        if any(
            (
                instance.distance_m is not None,
                instance.time_seconds is not None,
                instance.avg_hr is not None,
                bool(instance.note),
                bool(instance.feel),
            )
        ):
            return

        linked_activity_ids = {
            activity_id
            for activity_id in (
                getattr(planned, "activity_id", None),
                getattr(instance, "activity_id", None),
            )
            if activity_id is not None
        }
        instance.delete()
        if linked_activity_ids:
            Activity.objects.filter(id__in=linked_activity_ids).delete()

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
        _cleanup_completed_if_empty(completed)
        return "" if completed.distance_m is None else f"{completed.distance_m / 1000.0:.2f}"

    if field == "min":
        time_seconds = _parse_optional_minutes_to_seconds(value)
        _set_and_save_if_changed(completed, {"time_seconds": time_seconds})
        _cleanup_completed_if_empty(completed)
        if completed.time_seconds is None:
            return ""
        return str(int(round(completed.time_seconds / 60.0)))

    if field == "third":
        if not isinstance(value, str):
            raise ValueError("Invalid text value.")
        _set_and_save_if_changed(completed, {"note": value})
        _cleanup_completed_if_empty(completed)
        return value or ""

    if field == "avg_hr":
        avg_hr = _parse_optional_int(value)
        if avg_hr is not None and avg_hr < 0:
            raise ValueError("Invalid avg_hr value.")
        _set_and_save_if_changed(completed, {"avg_hr": avg_hr})
        _cleanup_completed_if_empty(completed)
        return completed.avg_hr

    if field == "max_hr":
        max_hr = _parse_optional_int(value)
        if max_hr is not None and max_hr < 0:
            raise ValueError("Invalid max_hr value.")
        feel = "" if max_hr is None else str(max_hr)
        _set_and_save_if_changed(completed, {"feel": feel})
        if getattr(planned, "activity", None):
            _set_and_save_if_changed(planned.activity, {"max_hr": max_hr})
        _cleanup_completed_if_empty(completed)
        return max_hr

    raise ValueError("Invalid field.")


