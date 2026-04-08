from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from dashboard.handlers.planned_training_api import (
    load_planned_training,
    parse_json_body,
    planned_athlete_id,
    save_planned_field,
    validate_completed_update_payload,
    validate_planned_update_payload,
)
from dashboard.services.month_cards import is_coach
from dashboard.api import json_error
from dashboard.texts import ApiText
from dashboard.views_shared import (
    _create_second_phase_for_planned,
    _remove_second_phase_for_planned,
    _update_completed_training_for_planned,
)


@login_required
@require_http_methods(["PATCH"])
def update_planned_training(request, planned_id: int):
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
