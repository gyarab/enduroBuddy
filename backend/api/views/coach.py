from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_http_methods

from accounts.services.notifications import notify_athlete_plan_updated
from accounts.models import CoachAthlete
from dashboard.api import json_error
from dashboard.handlers.planned_training_api import (
    load_planned_training,
    parse_json_body,
    planned_athlete_id,
    save_planned_field,
    validate_planned_id_payload,
    validate_planned_update_payload,
)
from dashboard.services.month_cards import display_name, is_coach
from dashboard.texts import ApiText, CoachText
from dashboard.views_shared import (
    _coach_can_access_athlete,
    _create_second_phase_for_planned,
    _get_cached_coach_accessible_ids,
    _remove_second_phase_for_planned,
)

from .dashboard import build_dashboard_payload_for_athlete


def _parse_athlete_id(raw_value):
    raw = (raw_value or "").strip()
    if not raw or not raw.isdigit():
        return None
    return int(raw)


def _coach_links_queryset(user):
    return user.coached_athletes.select_related("athlete").order_by("sort_order", "id")


def _serialize_coach_athlete_link(link, *, selected_athlete_id=None):
    return {
        "id": link.athlete_id,
        "name": display_name(link.athlete),
        "focus": (link.focus or "")[:10],
        "hidden": bool(link.hidden_from_plans),
        "sort_order": link.sort_order,
        "selected": link.athlete_id == selected_athlete_id,
    }


@login_required
@require_GET
def coach_dashboard(request):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)

    links = list(_coach_links_queryset(request.user))
    if not links:
        return JsonResponse(
            {
                "selected_athlete": None,
                "athletes": [],
                **build_dashboard_payload_for_athlete(
                    athlete=request.user,
                    language_code=getattr(request, "LANGUAGE_CODE", "cs"),
                    month_query=request.GET.get("month"),
                    flags={
                        "is_coach": True,
                        "can_edit_planned": True,
                        "can_edit_completed": False,
                    },
                ),
            }
        )

    requested_athlete_id = _parse_athlete_id(request.GET.get("athlete_id"))
    accessible_ids = _get_cached_coach_accessible_ids(request)
    if requested_athlete_id is not None and not _coach_can_access_athlete(
        coach_user=request.user,
        athlete_id=requested_athlete_id,
        accessible_ids=accessible_ids,
    ):
        return json_error(ApiText.FORBIDDEN_FOR_ATHLETE, status=403)

    selected_link = next((link for link in links if link.athlete_id == requested_athlete_id), None) if requested_athlete_id else links[0]
    if selected_link is None:
        selected_link = links[0]

    selected_athlete = selected_link.athlete
    dashboard_payload = build_dashboard_payload_for_athlete(
        athlete=selected_athlete,
        language_code=getattr(request, "LANGUAGE_CODE", "cs"),
        month_query=request.GET.get("month"),
        flags={
            "is_coach": True,
            "can_edit_planned": True,
            "can_edit_completed": False,
        },
    )

    athletes_payload = [
        _serialize_coach_athlete_link(link, selected_athlete_id=selected_athlete.id)
        for link in links
        if not bool(link.hidden_from_plans)
    ]

    return JsonResponse(
        {
            "selected_athlete": {
                "id": selected_athlete.id,
                "name": display_name(selected_athlete),
                "focus": (selected_link.focus or "")[:10],
            },
            "athletes": athletes_payload,
            **dashboard_payload,
        }
    )


@login_required
@require_GET
def coach_athletes(request):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)

    selected_athlete_id = _parse_athlete_id(request.GET.get("athlete_id"))
    links = list(_coach_links_queryset(request.user))
    return JsonResponse(
        {
            "athletes": [
                _serialize_coach_athlete_link(link, selected_athlete_id=selected_athlete_id)
                for link in links
            ]
        }
    )


@login_required
@require_http_methods(["PATCH"])
def coach_update_planned_training(request, planned_id: int):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)

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

    athlete_id = planned_athlete_id(planned)
    accessible_ids = _get_cached_coach_accessible_ids(request)
    if not _coach_can_access_athlete(coach_user=request.user, athlete_id=athlete_id, accessible_ids=accessible_ids):
        return json_error(ApiText.FORBIDDEN_FOR_ATHLETE, status=403)

    old_value = getattr(planned, field, "")
    normalized = save_planned_field(planned=planned, field=field, value=value)
    notify_athlete_plan_updated(
        planned=planned,
        actor=request.user,
        field=field,
        old_value=old_value,
        new_value=normalized,
    )
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
def coach_second_phase_training(request, planned_id: int):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)

    parsed_planned_id, error = validate_planned_id_payload({"planned_id": planned_id})
    if error:
        return error

    planned, error = load_planned_training(parsed_planned_id)
    if error:
        return error

    athlete_id = planned_athlete_id(planned)
    accessible_ids = _get_cached_coach_accessible_ids(request)
    if not _coach_can_access_athlete(coach_user=request.user, athlete_id=athlete_id, accessible_ids=accessible_ids):
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
@require_http_methods(["PATCH"])
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
@require_http_methods(["PATCH"])
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

    changed_links = [
        link for link in links.values() if link.sort_order != getattr(link, "_original_sort_order", link.sort_order)
    ]
    if changed_links:
        CoachAthlete.objects.bulk_update(changed_links, ["sort_order"])

    refreshed_links = list(_coach_links_queryset(request.user))
    return JsonResponse(
        {
            "ok": True,
            "athletes": [_serialize_coach_athlete_link(link) for link in refreshed_links],
        }
    )


@login_required
@require_http_methods(["PATCH"])
def coach_toggle_athlete_visibility(request):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return json_error(ApiText.INVALID_JSON_BODY, status=400)

    athlete_id = payload.get("athlete_id")
    hidden = payload.get("hidden")
    if not isinstance(athlete_id, int):
        return json_error(ApiText.INVALID_ATHLETE_ID, status=400)
    if not isinstance(hidden, bool):
        return json_error(ApiText.INVALID_VALUE, status=400)
    if athlete_id == request.user.id:
        return JsonResponse({"ok": False, "error": CoachText.CANNOT_HIDE_OWN_PLAN}, status=400)

    link = CoachAthlete.objects.select_related("athlete").filter(coach=request.user, athlete_id=athlete_id).first()
    if link is None:
        return json_error(ApiText.ATHLETE_LINK_NOT_FOUND, status=404)

    link.hidden_from_plans = hidden
    link.save(update_fields=["hidden_from_plans"])

    refreshed_links = list(_coach_links_queryset(request.user))
    return JsonResponse(
        {
            "ok": True,
            "athlete_id": athlete_id,
            "hidden": link.hidden_from_plans,
            "athletes": [_serialize_coach_athlete_link(item) for item in refreshed_links],
        }
    )
