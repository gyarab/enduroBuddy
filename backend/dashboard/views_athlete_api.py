from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from dashboard.api import json_error
from dashboard.handlers.planned_training_api import (
    load_planned_training,
    parse_json_body,
    planned_athlete_id,
    save_planned_field,
    validate_completed_update_payload,
    validate_planned_id_payload,
    validate_planned_update_payload,
)
from dashboard.texts import ApiText
from .views_shared import (
    _create_second_phase_for_planned,
    _remove_second_phase_for_planned,
    _update_completed_training_for_planned,
)


@login_required
@require_POST
def athlete_update_planned_training(request):
    payload, error = parse_json_body(request)
    if error:
        return error

    parsed_payload, error = validate_planned_update_payload(payload)
    if error:
        return error

    planned_id, field, value = parsed_payload
    planned, error = load_planned_training(planned_id)
    if error:
        return error
    if planned_athlete_id(planned) != request.user.id:
        return json_error(ApiText.FORBIDDEN_FOR_ATHLETE, status=403)

    save_planned_field(planned=planned, field=field, value=value)
    return JsonResponse({"ok": True, "planned_id": planned.id, "field": field, "value": value})


@login_required
@require_POST
def athlete_update_completed_training(request):
    payload, error = parse_json_body(request)
    if error:
        return error

    parsed_payload, error = validate_completed_update_payload(payload)
    if error:
        return error

    planned_id, field, value = parsed_payload
    planned, error = load_planned_training(planned_id, include_activity=True)
    if error:
        return error
    if planned_athlete_id(planned) != request.user.id:
        return json_error(ApiText.FORBIDDEN_FOR_ATHLETE, status=403)

    try:
        normalized = _update_completed_training_for_planned(planned=planned, field=field, value=value)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse({"ok": True, "planned_id": planned.id, "field": field, "value": normalized})


@login_required
@require_POST
def athlete_add_second_phase_training(request):
    payload, error = parse_json_body(request)
    if error:
        return error

    planned_id, error = validate_planned_id_payload(payload)
    if error:
        return error

    planned, error = load_planned_training(planned_id)
    if error:
        return error
    if planned_athlete_id(planned) != request.user.id:
        return json_error(ApiText.FORBIDDEN_FOR_ATHLETE, status=403)

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


@login_required
@require_POST
def athlete_remove_second_phase_training(request):
    payload, error = parse_json_body(request)
    if error:
        return error

    planned_id, error = validate_planned_id_payload(payload)
    if error:
        return error

    planned, error = load_planned_training(planned_id)
    if error:
        return error
    if planned_athlete_id(planned) != request.user.id:
        return json_error(ApiText.FORBIDDEN_FOR_ATHLETE, status=403)

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
