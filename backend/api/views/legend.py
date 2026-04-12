from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from dashboard.api import json_error
from dashboard.texts import ApiText
from dashboard.views_shared import sanitize_legend_state


@login_required
@require_http_methods(["GET", "POST"])
def legend(request):
    profile = request.user.profile
    if request.method == "GET":
        state = sanitize_legend_state(getattr(profile, "legend_state", {}))
        return JsonResponse({"ok": True, "state": state})

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return json_error(ApiText.INVALID_JSON_BODY, status=400)

    next_state = sanitize_legend_state(payload.get("state"))
    profile.legend_state = next_state
    profile.save(update_fields=["legend_state"])
    return JsonResponse({"ok": True, "state": next_state})
