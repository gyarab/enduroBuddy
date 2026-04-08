from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_http_methods

from accounts.models import CoachAthlete
from dashboard.api import json_error
from dashboard.services.month_cards import display_name, is_coach
from dashboard.texts import ApiText
from dashboard.views_shared import _coach_can_access_athlete, _get_cached_coach_accessible_ids

from .dashboard import build_dashboard_payload_for_athlete


def _parse_athlete_id(raw_value):
    raw = (raw_value or "").strip()
    if not raw or not raw.isdigit():
        return None
    return int(raw)


@login_required
@require_GET
def coach_dashboard(request):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)

    links = list(request.user.coached_athletes.select_related("athlete").order_by("sort_order", "id"))
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
                        "can_edit_planned": False,
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
            "can_edit_planned": False,
            "can_edit_completed": False,
        },
    )

    athletes_payload = [
        {
            "id": link.athlete_id,
            "name": display_name(link.athlete),
            "focus": (link.focus or "")[:10],
            "hidden": bool(link.hidden_from_plans),
            "sort_order": link.sort_order,
            "selected": link.athlete_id == selected_athlete.id,
        }
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
