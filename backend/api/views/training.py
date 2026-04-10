from __future__ import annotations

from datetime import date

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from accounts.models import CoachAthlete
from dashboard.handlers.planned_training_api import (
    load_planned_training,
    parse_json_body,
    planned_athlete_id,
    save_planned_field,
    validate_completed_update_payload,
    validate_planned_update_payload,
)
from dashboard.services.month_cards import add_next_month_for_athlete, is_coach, resolve_week_for_day
from dashboard.api import json_error
from dashboard.texts import ApiText
from dashboard.views_shared import (
    _create_second_phase_for_planned,
    _remove_second_phase_for_planned,
    _update_completed_training_for_planned,
)
from training.models import CompletedTraining, PlannedTraining


DAY_LABELS_CS = ["Po", "Ut", "St", "Ct", "Pa", "So", "Ne"]


def _parse_iso_date(raw_value):
    raw = str(raw_value or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def _clean_session_type(raw_value):
    value = str(raw_value or PlannedTraining.SessionType.RUN).strip()
    if value not in {PlannedTraining.SessionType.RUN, PlannedTraining.SessionType.WORKOUT}:
        return None
    return value


def _create_planned_training_for_athlete(*, athlete, payload: dict):
    run_day = _parse_iso_date(payload.get("date"))
    if run_day is None:
        return None, json_error("Invalid date.", status=400)

    session_type = _clean_session_type(payload.get("session_type"))
    if session_type is None:
        return None, json_error(ApiText.INVALID_SESSION_TYPE, status=400)

    existing_day_items = PlannedTraining.objects.filter(
        week__training_month__athlete=athlete,
        date=run_day,
    ).order_by("order_in_day", "id")
    if existing_day_items.exists():
        return None, json_error("Planned training already exists for this day. Use second-phase flow for two-phase days.", status=400)

    week = resolve_week_for_day(athlete, run_day)
    planned = PlannedTraining.objects.create(
        week=week,
        date=run_day,
        day_label=DAY_LABELS_CS[run_day.weekday()],
        title=str(payload.get("title") or "").strip(),
        notes=str(payload.get("notes") or "").strip(),
        session_type=session_type,
        order_in_day=1,
    )
    return planned, None


def _serialize_planned_mutation(planned: PlannedTraining) -> dict:
    return {
        "id": planned.id,
        "date": planned.date.isoformat() if planned.date else None,
        "day_label": planned.day_label,
        "title": planned.title,
        "notes": planned.notes,
        "session_type": planned.session_type,
        "is_second_phase": planned.order_in_day > 1 or planned.is_two_phase_day,
    }


def _delete_planned_training_for_actor(*, planned: PlannedTraining):
    has_linked_activity = False
    try:
        has_linked_activity = planned.activity is not None
    except ObjectDoesNotExist:
        has_linked_activity = False

    if CompletedTraining.objects.filter(planned=planned).exists() or has_linked_activity:
        return None, json_error("Cannot delete planned training with completed or linked activity data.", status=400)

    day_items = list(
        PlannedTraining.objects.filter(week=planned.week, date=planned.date).order_by("order_in_day", "id")
    )
    if len(day_items) > 1:
        if planned.id == day_items[-1].id:
            try:
                removed_planned_id = _remove_second_phase_for_planned(planned=planned)
            except ValueError as exc:
                return None, JsonResponse({"ok": False, "error": str(exc)}, status=400)
            return removed_planned_id, None
        return None, json_error("Cannot delete the first phase while a second phase exists.", status=400)

    removed_planned_id = planned.id
    planned.delete()
    return removed_planned_id, None


@login_required
@require_http_methods(["POST"])
def create_planned_training(request):
    if is_coach(request.user):
        return json_error(ApiText.FORBIDDEN_FOR_ATHLETE, status=403)

    payload, error = parse_json_body(request)
    if error:
        return error
    if not isinstance(payload, dict):
        return json_error(ApiText.INVALID_JSON_BODY, status=400)

    planned, error = _create_planned_training_for_athlete(athlete=request.user, payload=payload)
    if error:
        return error

    return JsonResponse({"ok": True, "planned": _serialize_planned_mutation(planned)}, status=201)


@login_required
@require_http_methods(["PATCH", "DELETE"])
def update_planned_training(request, planned_id: int):
    if request.method == "DELETE":
        planned, error = load_planned_training(planned_id)
        if error:
            return error
        if planned_athlete_id(planned) != request.user.id or is_coach(request.user):
            return json_error(ApiText.FORBIDDEN_FOR_ATHLETE, status=403)
        removed_planned_id, error = _delete_planned_training_for_actor(planned=planned)
        if error:
            return error
        return JsonResponse({"ok": True, "removed_planned_id": removed_planned_id})

    payload, error = parse_json_body(request)
    if error:
        return error

    payload = {
        **payload,
        "planned_id": planned_id,
    }
    parsed_payload, error = validate_planned_update_payload(payload)
    if error:
        return error

    parsed_planned_id, field, value = parsed_payload
    planned, error = load_planned_training(parsed_planned_id)
    if error:
        return error

    if planned_athlete_id(planned) != request.user.id or is_coach(request.user):
        return json_error(ApiText.FORBIDDEN_FOR_ATHLETE, status=403)

    normalized = save_planned_field(planned=planned, field=field, value=value)
    return JsonResponse(
        {
            "ok": True,
            "planned_id": planned.id,
            "field": field,
            "value": normalized,
        }
    )


@login_required
@require_http_methods(["PATCH"])
def update_completed_training(request, planned_id: int):
    payload, error = parse_json_body(request)
    if error:
        return error

    payload = {
        **payload,
        "planned_id": planned_id,
    }
    parsed_payload, error = validate_completed_update_payload(payload)
    if error:
        return error

    parsed_planned_id, field, value = parsed_payload
    planned, error = load_planned_training(parsed_planned_id, include_activity=True)
    if error:
        return error

    if planned_athlete_id(planned) != request.user.id or is_coach(request.user):
        return json_error(ApiText.FORBIDDEN_FOR_ATHLETE, status=403)

    try:
        normalized = _update_completed_training_for_planned(planned=planned, field=field, value=value)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse(
        {
            "ok": True,
            "planned_id": planned.id,
            "field": field,
            "value": normalized,
        }
    )


@login_required
@require_http_methods(["POST", "DELETE"])
def second_phase_training(request, planned_id: int):
    planned, error = load_planned_training(planned_id)
    if error:
        return error

    if planned_athlete_id(planned) != request.user.id or is_coach(request.user):
        return json_error(ApiText.FORBIDDEN_FOR_ATHLETE, status=403)

    if request.method == "POST":
        try:
            created = _create_second_phase_for_planned(planned=planned)
        except ValueError as exc:
            return JsonResponse({"ok": False, "error": str(exc)}, status=400)

        return JsonResponse(
            {
                "ok": True,
                "planned_id": planned.id,
                "second_phase_planned_id": created.id,
            }
        )

    try:
        removed_planned_id = _remove_second_phase_for_planned(planned=planned)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse(
        {
            "ok": True,
            "planned_id": planned.id,
            "removed_planned_id": removed_planned_id,
        }
    )


@login_required
@require_http_methods(["POST"])
def add_next_month(request):
    payload, error = parse_json_body(request)
    if error:
        return error

    athlete_id = (payload or {}).get("athlete_id")

    if is_coach(request.user):
        if not athlete_id:
            return json_error(ApiText.INVALID_ATHLETE_ID, status=400)
        link = CoachAthlete.objects.filter(coach=request.user, athlete_id=athlete_id).first()
        if link is None:
            return json_error(ApiText.FORBIDDEN_FOR_ATHLETE, status=403)
        target_athlete = link.athlete
    else:
        target_athlete = request.user

    month_created, weeks_created, days_created = add_next_month_for_athlete(athlete=target_athlete)
    return JsonResponse({
        "ok": True,
        "month_created": month_created,
        "weeks_created": weeks_created,
        "days_created": days_created,
    })
