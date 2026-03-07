from __future__ import annotations

import json
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from dashboard.services.planned_km import estimate_running_km_from_title
from training.models import PlannedTraining
from .views_shared import (
    _create_second_phase_for_planned,
    _remove_second_phase_for_planned,
    _update_completed_training_for_planned,
)

_MAX_PLANNED_DISTANCE_KM = Decimal("999.99")

@login_required
@require_POST
def athlete_update_planned_training(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)

    planned_id = payload.get("planned_id")
    field = payload.get("field")
    value = payload.get("value", "")

    if not isinstance(planned_id, int):
        return JsonResponse({"ok": False, "error": "Invalid planned_id."}, status=400)
    if field not in {"title", "notes"}:
        return JsonResponse({"ok": False, "error": "Invalid field."}, status=400)
    if not isinstance(value, str):
        return JsonResponse({"ok": False, "error": "Invalid value."}, status=400)

    planned = (
        PlannedTraining.objects.select_related("week__training_month")
        .filter(id=planned_id)
        .first()
    )
    if planned is None:
        return JsonResponse({"ok": False, "error": "Planned training not found."}, status=404)

    if planned.week.training_month.athlete_id != request.user.id:
        return JsonResponse({"ok": False, "error": "Forbidden for this athlete."}, status=403)

    setattr(planned, field, value)
    update_fields = [field]
    if field == "title":
        estimated = estimate_running_km_from_title(value)
        if estimated is not None:
            estimated = min(estimated, _MAX_PLANNED_DISTANCE_KM)
        planned.planned_distance_km = estimated
        update_fields.append("planned_distance_km")
    planned.save(update_fields=update_fields)
    return JsonResponse({"ok": True, "planned_id": planned.id, "field": field, "value": value})



@login_required
@require_POST
def athlete_update_completed_training(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)

    planned_id = payload.get("planned_id")
    field = payload.get("field")
    value = payload.get("value", "")

    if not isinstance(planned_id, int):
        return JsonResponse({"ok": False, "error": "Invalid planned_id."}, status=400)
    if field not in {"km", "min", "third", "avg_hr", "max_hr"}:
        return JsonResponse({"ok": False, "error": "Invalid field."}, status=400)

    planned = PlannedTraining.objects.select_related("week__training_month", "activity").filter(id=planned_id).first()
    if planned is None:
        return JsonResponse({"ok": False, "error": "Planned training not found."}, status=404)
    if planned.week.training_month.athlete_id != request.user.id:
        return JsonResponse({"ok": False, "error": "Forbidden for this athlete."}, status=403)

    try:
        normalized = _update_completed_training_for_planned(planned=planned, field=field, value=value)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse({"ok": True, "planned_id": planned.id, "field": field, "value": normalized})


@login_required
@require_POST
def athlete_add_second_phase_training(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)

    planned_id = payload.get("planned_id")
    if not isinstance(planned_id, int):
        return JsonResponse({"ok": False, "error": "Invalid planned_id."}, status=400)

    planned = (
        PlannedTraining.objects.select_related("week__training_month")
        .filter(id=planned_id)
        .first()
    )
    if planned is None:
        return JsonResponse({"ok": False, "error": "Planned training not found."}, status=404)
    if planned.week.training_month.athlete_id != request.user.id:
        return JsonResponse({"ok": False, "error": "Forbidden for this athlete."}, status=403)

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
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)

    planned_id = payload.get("planned_id")
    if not isinstance(planned_id, int):
        return JsonResponse({"ok": False, "error": "Invalid planned_id."}, status=400)

    planned = (
        PlannedTraining.objects.select_related("week__training_month")
        .filter(id=planned_id)
        .first()
    )
    if planned is None:
        return JsonResponse({"ok": False, "error": "Planned training not found."}, status=404)
    if planned.week.training_month.athlete_id != request.user.id:
        return JsonResponse({"ok": False, "error": "Forbidden for this athlete."}, status=403)

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


