from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from accounts.models import CoachAthlete
from accounts.services.notifications import notify_athlete_plan_updated
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
from dashboard.services.month_cards import is_coach
from dashboard.texts import ApiText

from .views_shared import (
    _coach_can_access_athlete,
    _create_second_phase_for_planned,
    _get_cached_coach_accessible_ids,
    _remove_second_phase_for_planned,
    _update_completed_training_for_planned,
)


@login_required
@require_POST
def coach_update_planned_training(request):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)

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

    athlete_id = planned_athlete_id(planned)
    accessible_ids = _get_cached_coach_accessible_ids(request)
    if not _coach_can_access_athlete(coach_user=request.user, athlete_id=athlete_id, accessible_ids=accessible_ids):
        return json_error(ApiText.FORBIDDEN_FOR_ATHLETE, status=403)

    old_value = getattr(planned, field, "")
    save_planned_field(planned=planned, field=field, value=value)
    notify_athlete_plan_updated(
        planned=planned,
        actor=request.user,
        field=field,
        old_value=old_value,
        new_value=value,
    )
    return JsonResponse({"ok": True, "planned_id": planned.id, "field": field, "value": value})


@login_required
@require_POST
def coach_update_completed_training(request):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)

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

    athlete_id = planned_athlete_id(planned)
    accessible_ids = _get_cached_coach_accessible_ids(request)
    if not _coach_can_access_athlete(coach_user=request.user, athlete_id=athlete_id, accessible_ids=accessible_ids):
        return json_error(ApiText.FORBIDDEN_FOR_ATHLETE, status=403)
    if athlete_id != request.user.id:
        return json_error(ApiText.COACH_CANNOT_EDIT_MANAGED_COMPLETED, status=403)

    try:
        normalized = _update_completed_training_for_planned(planned=planned, field=field, value=value)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse({"ok": True, "planned_id": planned.id, "field": field, "value": normalized})


@login_required
@require_POST
def coach_add_second_phase_training(request):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)

    payload, error = parse_json_body(request)
    if error:
        return error
    planned_id, error = validate_planned_id_payload(payload)
    if error:
        return error

    planned, error = load_planned_training(planned_id)
    if error:
        return error

    athlete_id = planned_athlete_id(planned)
    accessible_ids = _get_cached_coach_accessible_ids(request)
    if not _coach_can_access_athlete(coach_user=request.user, athlete_id=athlete_id, accessible_ids=accessible_ids):
        return json_error(ApiText.FORBIDDEN_FOR_ATHLETE, status=403)

    try:
        created = _create_second_phase_for_planned(planned=planned)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse({"ok": True, "planned_id": planned.id, "second_phase_planned_id": created.id})


@login_required
@require_POST
def coach_remove_second_phase_training(request):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)

    payload, error = parse_json_body(request)
    if error:
        return error
    planned_id, error = validate_planned_id_payload(payload)
    if error:
        return error

    planned, error = load_planned_training(planned_id)
    if error:
        return error

    athlete_id = planned_athlete_id(planned)
    accessible_ids = _get_cached_coach_accessible_ids(request)
    if not _coach_can_access_athlete(coach_user=request.user, athlete_id=athlete_id, accessible_ids=accessible_ids):
        return json_error(ApiText.FORBIDDEN_FOR_ATHLETE, status=403)

    try:
        removed_planned_id = _remove_second_phase_for_planned(planned=planned)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse({"ok": True, "planned_id": planned.id, "removed_planned_id": removed_planned_id})


@login_required
@require_POST
def coach_update_athlete_focus(request):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return json_error(ApiText.INVALID_JSON_BODY, status=400)

    athlete_id = payload.get("athlete_id")
    focus = payload.get("focus", "")
    if not isinstance(athlete_id, int):
        return json_error(ApiText.INVALID_ATHLETE_ID, status=400)
    if not isinstance(focus, str):
        return json_error(ApiText.INVALID_FOCUS_VALUE, status=400)

    link = CoachAthlete.objects.filter(coach=request.user, athlete_id=athlete_id).first()
    if link is None:
        return json_error(ApiText.ATHLETE_LINK_NOT_FOUND, status=404)

    link.focus = focus.strip()[:10]
    link.save(update_fields=["focus"])
    return JsonResponse({"ok": True, "athlete_id": athlete_id, "focus": link.focus})


@login_required
@require_POST
def coach_reorder_athletes(request):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return json_error(ApiText.INVALID_JSON_BODY, status=400)

    athlete_ids = payload.get("athlete_ids")
    if not isinstance(athlete_ids, list) or not all(isinstance(x, int) for x in athlete_ids):
        return json_error(ApiText.ATHLETE_IDS_MUST_BE_INT_LIST, status=400)
    if len(set(athlete_ids)) != len(athlete_ids):
        return json_error(ApiText.DUPLICATE_ATHLETE_IDS, status=400)

    links = {}
    for link in CoachAthlete.objects.filter(coach=request.user, athlete_id__in=athlete_ids):
        link._original_sort_order = link.sort_order
        links[link.athlete_id] = link
    if len(links) != len(athlete_ids):
        return json_error(ApiText.UNLINKED_ATHLETE_IDS, status=403)

    for index, athlete_id in enumerate(athlete_ids, start=1):
        links[athlete_id].sort_order = index

    changed_links = [link for link in links.values() if link.sort_order != getattr(link, "_original_sort_order", link.sort_order)]
    if not changed_links:
        return JsonResponse({"ok": True})

    CoachAthlete.objects.bulk_update(changed_links, ["sort_order"])
    return JsonResponse({"ok": True})
