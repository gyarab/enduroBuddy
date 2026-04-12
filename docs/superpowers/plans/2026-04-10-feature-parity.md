# Feature Parity — Missing Buttons & Functions

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the ~30 % of Django app features missing from the Vue SPA: legend management, coach code/join requests, add-month, Garmin week sync, group invite, KM popover, linked-activity lock.

**Architecture:** Backend adds thin API wrappers over existing service functions; frontend extends existing stores and components. All new Vue code uses scoped CSS + `useI18n()`. No new dependencies.

**Tech Stack:** Django 5.2 + DRF-style function views, Vue 3 + TypeScript, Pinia, axios, Vitest.

**Verification after every backend task:** `cd /c/Users/admin/projects/enduroBuddy-personal && python backend/manage.py check --deploy 2>&1 | head -5` must show no errors.
**Verification after every frontend task:** `cd /c/Users/admin/projects/enduroBuddy-personal/frontend && npm run build 2>&1 | tail -5` must show `✓ built`.

---

## File Map

### Backend — new/modified
| File | Change |
|------|--------|
| `backend/api/views/legend.py` | New — GET + POST legend state |
| `backend/api/views/imports.py` | Add `garmin_week_sync` function |
| `backend/api/views/training.py` | Add `add_next_month` function |
| `backend/api/views/coach.py` | Add coach_code, join_requests, remove_athlete |
| `backend/api/views/invites.py` | New — GET invite info + POST accept |
| `backend/api/views/dashboard.py` | Extend `_serialize_planned_row` with KM detail fields |
| `backend/api/urls.py` | Register all new endpoints |

### Frontend — new/modified
| File | Change |
|------|--------|
| `frontend/src/api/legend.ts` | New — fetchLegend, saveLegend |
| `frontend/src/api/invites.ts` | New — fetchInvite, acceptInvite |
| `frontend/src/api/coach.ts` | Add fetchCoachCode, fetchJoinRequests, approveRequest, rejectRequest, removeAthlete, requestCoachByCode |
| `frontend/src/api/imports.ts` | Add garminWeekSync |
| `frontend/src/api/training.ts` | Add addNextMonth; extend TrainingRow type |
| `frontend/src/stores/legend.ts` | New — legend Pinia store |
| `frontend/src/stores/coach.ts` | Add join request + remove athlete actions |
| `frontend/src/components/layout/TopNav.vue` | Add legend button |
| `frontend/src/components/layout/LegendModal.vue` | New — HR zones, thresholds, PRs |
| `frontend/src/components/coach/AthleteManageModal.vue` | Add Code + Requests tabs; remove athlete |
| `frontend/src/components/training/WeekCard.vue` | Add Garmin week sync button |
| `frontend/src/components/training/PlannedRow.vue` | Add KM detail popover |
| `frontend/src/components/training/CompletedRow.vue` | Add linked-activity lock badge |
| `frontend/src/components/training/CompletedEditor.vue` | Disable when has_linked_activity |
| `frontend/src/views/dashboard/AthleteView.vue` | Add month button + request-coach widget |
| `frontend/src/views/dashboard/CoachView.vue` | Add month button |
| `frontend/src/views/invite/InviteView.vue` | New — accept group invite |
| `frontend/src/router/index.ts` | Add /coach/invite/:token route |
| `frontend/src/locales/cs.json` | New keys for all new UI |
| `frontend/src/locales/en.json` | New keys for all new UI |

---

## Task 1: Backend — Legend API endpoint

**Files:**
- Create: `backend/api/views/legend.py`
- Modify: `backend/api/urls.py`

- [ ] **Step 1: Create `backend/api/views/legend.py`**

```python
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
```

- [ ] **Step 2: Register in `backend/api/urls.py`**

Add at the top with other imports:
```python
from .views.legend import legend
```

Add to `urlpatterns`:
```python
path("legend/", legend, name="api_legend"),
```

- [ ] **Step 3: Verify**

```bash
cd /c/Users/admin/projects/enduroBuddy-personal && python backend/manage.py check 2>&1 | tail -3
```
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 4: Commit**

```bash
git add backend/api/views/legend.py backend/api/urls.py
git commit -m "feat(api): add legend GET/POST endpoint"
```

---

## Task 2: Backend — Garmin week sync API endpoint

**Files:**
- Modify: `backend/api/views/imports.py`
- Modify: `backend/api/urls.py`

- [ ] **Step 1: Add `garmin_week_sync` to `backend/api/views/imports.py`**

Add at the top with other imports:
```python
from datetime import date, timedelta
from django.utils import timezone
from dashboard.services.imports import sync_garmin_week_for_user
from dashboard.texts import HomeText
```

Add after the `fit_upload` function:
```python
@login_required
@require_POST
def garmin_week_sync(request):
    if not settings.GARMIN_SYNC_ENABLED:
        return json_error(ApiText.GARMIN_SYNC_DISABLED, status=503)

    payload, error = _parse_json_body(request)
    if error:
        return error

    raw_week_start = str((payload or {}).get("week_start") or "").strip()
    try:
        week_start = date.fromisoformat(raw_week_start)
    except ValueError:
        return json_error("Invalid week_start date.", status=400)

    if not GarminConnection.objects.filter(user=request.user, is_active=True).exists():
        return json_error(ApiText.GARMIN_NOT_CONNECTED, status=400)

    normalized = week_start - timedelta(days=week_start.weekday())
    if normalized > timezone.localdate():
        return json_error("Week has not started yet.", status=400)

    try:
        replaced, untouched, _conn = sync_garmin_week_for_user(request.user, week_start=normalized)
    except Exception:
        return json_error("Garmin week sync failed.", status=500)

    return JsonResponse({
        "ok": True,
        "replaced": replaced,
        "untouched": untouched,
        "message": HomeText.garmin_week_synced(replaced=replaced, untouched=untouched),
    })
```

- [ ] **Step 2: Register in `backend/api/urls.py`**

Add import:
```python
from .views.imports import fit_upload, garmin_connect, garmin_revoke, garmin_sync_start, garmin_week_sync, import_job_status
```

Add to `urlpatterns`:
```python
path("imports/garmin/week-sync/", garmin_week_sync, name="api_imports_garmin_week_sync"),
```

- [ ] **Step 3: Verify**

```bash
cd /c/Users/admin/projects/enduroBuddy-personal && python backend/manage.py check 2>&1 | tail -3
```
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 4: Commit**

```bash
git add backend/api/views/imports.py backend/api/urls.py
git commit -m "feat(api): add garmin week sync endpoint"
```

---

## Task 3: Backend — Add next month API endpoint

**Files:**
- Modify: `backend/api/views/training.py`
- Modify: `backend/api/urls.py`

- [ ] **Step 1: Add `add_next_month` to `backend/api/views/training.py`**

Add to imports at the top:
```python
from dashboard.services.month_cards import add_next_month_for_athlete
```

Add after existing functions:
```python
@login_required
@require_http_methods(["POST"])
def add_next_month(request):
    payload, error = parse_json_body(request)
    if error:
        return error

    athlete_id = (payload or {}).get("athlete_id")

    if athlete_id is not None:
        # Coach creating month for an athlete
        if not is_coach(request.user):
            return json_error(ApiText.COACH_ACCESS_ONLY, status=403)
        from accounts.models import CoachAthlete
        link = CoachAthlete.objects.filter(coach=request.user, athlete_id=athlete_id).first()
        if link is None:
            return json_error("Athlete not found.", status=404)
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
```

Also add the missing import at the top of the file:
```python
from django.views.decorators.http import require_http_methods
```

- [ ] **Step 2: Register in `backend/api/urls.py`**

Add import:
```python
from .views.training import add_next_month, create_planned_training, second_phase_training, update_completed_training, update_planned_training
```

Add to `urlpatterns`:
```python
path("training/months/", add_next_month, name="api_training_months_add"),
```

- [ ] **Step 3: Verify**

```bash
cd /c/Users/admin/projects/enduroBuddy-personal && python backend/manage.py check 2>&1 | tail -3
```

- [ ] **Step 4: Commit**

```bash
git add backend/api/views/training.py backend/api/urls.py
git commit -m "feat(api): add next month creation endpoint"
```

---

## Task 4: Backend — Coach code + join requests endpoints

**Files:**
- Modify: `backend/api/views/coach.py`
- Modify: `backend/api/urls.py`

- [ ] **Step 1: Add coach code + join request functions to `backend/api/views/coach.py`**

Add to imports at the top of `coach.py`:
```python
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from accounts.models import CoachAthlete, CoachJoinRequest, Role, TrainingGroupAthlete
from accounts.services.notifications import notify_new_coach_join_request
from dashboard.services.month_cards import add_next_month_for_athlete, display_name, is_coach
```

Add these functions after the existing ones:

```python
@login_required
@require_GET
def coach_code(request):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)
    code = request.user.profile.ensure_coach_join_code()
    return JsonResponse({"ok": True, "coach_join_code": code})


@login_required
@require_GET
def coach_join_requests_list(request):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)
    requests_qs = (
        CoachJoinRequest.objects.select_related("athlete")
        .filter(coach=request.user, status=CoachJoinRequest.Status.PENDING)
        .order_by("-created_at")
    )
    return JsonResponse({
        "ok": True,
        "join_requests": [
            {
                "id": jr.id,
                "athlete_name": display_name(jr.athlete),
                "athlete_username": jr.athlete.username,
                "created_at": jr.created_at.isoformat(),
            }
            for jr in requests_qs
        ],
    })


@login_required
@require_POST
def coach_join_request_approve(request, request_id: int):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)
    jr = (
        CoachJoinRequest.objects.select_related("athlete")
        .filter(id=request_id, coach=request.user, status=CoachJoinRequest.Status.PENDING)
        .first()
    )
    if jr is None:
        return json_error("Join request not found.", status=404)

    from accounts.models import TrainingGroupAthlete
    groups = list(request.user.training_groups.all())
    if groups:
        TrainingGroupAthlete.objects.get_or_create(group=groups[0], athlete=jr.athlete)

    from django.db.models import Max
    max_order = CoachAthlete.objects.filter(coach=request.user).aggregate(max_order=Max("sort_order")).get("max_order") or 0
    CoachAthlete.objects.get_or_create(
        coach=request.user,
        athlete=jr.athlete,
        defaults={"sort_order": int(max_order) + 1},
    )
    jr.status = CoachJoinRequest.Status.APPROVED
    jr.decided_at = timezone.now()
    jr.save(update_fields=["status", "decided_at"])
    return JsonResponse({"ok": True, "request_id": request_id})


@login_required
@require_POST
def coach_join_request_reject(request, request_id: int):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)
    jr = CoachJoinRequest.objects.filter(
        id=request_id, coach=request.user, status=CoachJoinRequest.Status.PENDING
    ).first()
    if jr is None:
        return json_error("Join request not found.", status=404)
    jr.status = CoachJoinRequest.Status.REJECTED
    jr.decided_at = timezone.now()
    jr.save(update_fields=["status", "decided_at"])
    return JsonResponse({"ok": True, "request_id": request_id})


@login_required
@require_POST
def athlete_request_coach(request):
    payload, error = parse_json_body(request)
    if error:
        return error
    coach_code_raw = str((payload or {}).get("coach_code") or "").strip().upper()
    if not coach_code_raw:
        return json_error("Coach code is required.", status=400)

    from accounts.models import Profile
    coach_profile = Profile.objects.filter(coach_join_code=coach_code_raw).select_related("user").first()
    if coach_profile is None:
        return json_error("Coach code not found.", status=404)
    coach_user = coach_profile.user

    if coach_user == request.user:
        return json_error("You cannot request yourself as a coach.", status=400)

    already_pending = CoachJoinRequest.objects.filter(
        coach=coach_user, athlete=request.user, status=CoachJoinRequest.Status.PENDING
    ).exists()
    if already_pending:
        return json_error("You already have a pending request for this coach.", status=409)

    jr = CoachJoinRequest.objects.create(
        coach=coach_user,
        athlete=request.user,
        status=CoachJoinRequest.Status.PENDING,
    )
    notify_new_coach_join_request(join_request=jr)
    return JsonResponse({"ok": True, "message": "Request sent."})


@login_required
def coach_remove_athlete(request, athlete_id: int):
    if request.method != "DELETE":
        return json_error(ApiText.METHOD_NOT_ALLOWED, status=405)
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)
    if athlete_id == request.user.id:
        return json_error("Cannot remove yourself.", status=400)

    import json as _json
    try:
        payload = _json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, _json.JSONDecodeError):
        return json_error(ApiText.INVALID_JSON_BODY, status=400)

    confirm_name = str((payload or {}).get("confirm_name") or "").strip()
    link = CoachAthlete.objects.select_related("athlete").filter(
        coach=request.user, athlete_id=athlete_id
    ).first()
    if link is None:
        return json_error("Athlete not found.", status=404)

    expected_name = display_name(link.athlete).strip()
    if confirm_name != expected_name:
        return json_error("Name confirmation does not match.", status=400)

    TrainingGroupAthlete.objects.filter(group__coach=request.user, athlete_id=athlete_id).delete()
    CoachJoinRequest.objects.filter(
        coach=request.user, athlete_id=athlete_id, status=CoachJoinRequest.Status.PENDING
    ).update(status=CoachJoinRequest.Status.REJECTED, decided_at=timezone.now())
    link.delete()
    return JsonResponse({"ok": True})
```

Also add `parse_json_body` to the imports from `dashboard.handlers.planned_training_api`.

- [ ] **Step 2: Register in `backend/api/urls.py`**

Add imports:
```python
from .views.coach import (
    coach_athletes,
    coach_code,
    coach_create_planned_training,
    coach_dashboard,
    coach_join_request_approve,
    coach_join_request_reject,
    coach_join_requests_list,
    coach_remove_athlete,
    coach_reorder_athletes,
    coach_second_phase_training,
    coach_toggle_athlete_visibility,
    coach_update_athlete_focus,
    coach_update_completed_training,
    coach_update_planned_training,
    athlete_request_coach,
)
```

Add to `urlpatterns`:
```python
path("coach/code/", coach_code, name="api_coach_code"),
path("coach/join-requests/", coach_join_requests_list, name="api_coach_join_requests"),
path("coach/join-requests/<int:request_id>/approve/", coach_join_request_approve, name="api_coach_join_request_approve"),
path("coach/join-requests/<int:request_id>/reject/", coach_join_request_reject, name="api_coach_join_request_reject"),
path("coach/join-request/", athlete_request_coach, name="api_athlete_request_coach"),
path("coach/athletes/<int:athlete_id>/", coach_remove_athlete, name="api_coach_remove_athlete"),
```

- [ ] **Step 3: Verify**

```bash
cd /c/Users/admin/projects/enduroBuddy-personal && python backend/manage.py check 2>&1 | tail -3
```

- [ ] **Step 4: Commit**

```bash
git add backend/api/views/coach.py backend/api/urls.py
git commit -m "feat(api): add coach code, join requests, and remove athlete endpoints"
```

---

## Task 5: Backend — Training group invite API endpoints

**Files:**
- Create: `backend/api/views/invites.py`
- Modify: `backend/api/urls.py`

- [ ] **Step 1: Create `backend/api/views/invites.py`**

```python
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from accounts.models import CoachAthlete, TrainingGroupAthlete, TrainingGroupInvite
from dashboard.api import json_error


def _serialize_invite(invite, *, is_expired: bool, is_used: bool) -> dict:
    return {
        "group_name": invite.group.name if invite.group else "",
        "coach_name": invite.group.coach.get_full_name() or invite.group.coach.username if invite.group else "",
        "is_expired": is_expired,
        "is_used": is_used,
    }


@login_required
@require_http_methods(["GET"])
def invite_detail(request, token: str):
    invite = (
        TrainingGroupInvite.objects.select_related("group", "group__coach")
        .filter(token=token)
        .first()
    )
    if invite is None:
        return json_error("Invite not found.", status=404)

    is_expired = invite.expires_at <= timezone.now()
    is_used = invite.used_at is not None
    return JsonResponse({"ok": True, "invite": _serialize_invite(invite, is_expired=is_expired, is_used=is_used)})


@login_required
@require_POST
def invite_accept(request, token: str):
    invite = (
        TrainingGroupInvite.objects.select_related("group", "group__coach")
        .filter(token=token)
        .first()
    )
    if invite is None:
        return json_error("Invite not found.", status=404)

    if invite.used_at is not None:
        return json_error("This invite has already been used.", status=409)
    if invite.expires_at <= timezone.now():
        return json_error("This invite has expired.", status=410)
    if request.user.id == invite.group.coach_id:
        return json_error("Coach cannot accept their own invite.", status=400)

    TrainingGroupAthlete.objects.get_or_create(group=invite.group, athlete=request.user)
    CoachAthlete.objects.get_or_create(coach=invite.group.coach, athlete=request.user)
    invite.used_at = timezone.now()
    invite.used_by = request.user
    invite.save(update_fields=["used_at", "used_by"])
    return JsonResponse({"ok": True, "message": "Invitation accepted."})
```

- [ ] **Step 2: Register in `backend/api/urls.py`**

Add import:
```python
from .views.invites import invite_accept, invite_detail
```

Add to `urlpatterns`:
```python
path("invites/<str:token>/", invite_detail, name="api_invite_detail"),
path("invites/<str:token>/accept/", invite_accept, name="api_invite_accept"),
```

- [ ] **Step 3: Verify**

```bash
cd /c/Users/admin/projects/enduroBuddy-personal && python backend/manage.py check 2>&1 | tail -3
```

- [ ] **Step 4: Commit**

```bash
git add backend/api/views/invites.py backend/api/urls.py
git commit -m "feat(api): add training group invite endpoints"
```

---

## Task 6: Backend — Extend planned row serializer with KM detail fields

**Files:**
- Modify: `backend/api/views/dashboard.py`

- [ ] **Step 1: Update `_serialize_planned_row` in `backend/api/views/dashboard.py`**

Find the `_serialize_planned_row` function (around line 59). Change `planned_metrics` from:
```python
        "planned_metrics": {
            "planned_km_value": row.get("planned_km_value") or 0,
            "planned_km_text": row.get("planned_km_text") or "",
            "planned_km_confidence": row.get("planned_km_confidence") or "low",
        },
```
To:
```python
        "planned_metrics": {
            "planned_km_value": row.get("planned_km_value") or 0,
            "planned_km_text": row.get("planned_km_text") or "",
            "planned_km_confidence": row.get("planned_km_confidence") or "low",
            "planned_km_show": bool(row.get("planned_km_show")),
            "planned_km_detail_km": row.get("planned_km_line_km") or "",
            "planned_km_detail_reason": row.get("planned_km_line_reason") or "",
            "planned_km_detail_where": row.get("planned_km_line_where") or "",
        },
```

- [ ] **Step 2: Verify**

```bash
cd /c/Users/admin/projects/enduroBuddy-personal && python backend/manage.py check 2>&1 | tail -3
```

- [ ] **Step 3: Commit**

```bash
git add backend/api/views/dashboard.py
git commit -m "feat(api): expose planned KM detail fields in dashboard response"
```

---

## Task 7: Frontend — API modules

**Files:**
- Create: `frontend/src/api/legend.ts`
- Create: `frontend/src/api/invites.ts`
- Modify: `frontend/src/api/coach.ts`
- Modify: `frontend/src/api/imports.ts`
- Modify: `frontend/src/api/training.ts`

- [ ] **Step 1: Create `frontend/src/api/legend.ts`**

```typescript
import { apiClient } from "@/api/client";

export type LegendZone = { from: string; to: string };

export type LegendState = {
  zones?: {
    z1?: LegendZone;
    z2?: LegendZone;
    z3?: LegendZone;
    z4?: LegendZone;
    z5?: LegendZone;
  };
  aerobic_threshold?: string;
  anaerobic_threshold?: string;
  prs?: Array<{ distance: string; time: string }>;
};

export const PR_DISTANCES = [
  "800m", "1000m", "1 mile", "1500m", "2 miles", "3000m", "3k",
  "5000m", "5k", "10000m", "10k", "Půlmaraton", "Maraton",
] as const;

export async function fetchLegend() {
  const response = await apiClient.get<{ ok: boolean; state: LegendState }>("/legend/");
  return response.data;
}

export async function saveLegend(state: LegendState) {
  const response = await apiClient.post<{ ok: boolean; state: LegendState }>("/legend/", { state });
  return response.data;
}
```

- [ ] **Step 2: Create `frontend/src/api/invites.ts`**

```typescript
import { apiClient } from "@/api/client";

export type InviteDetail = {
  group_name: string;
  coach_name: string;
  is_expired: boolean;
  is_used: boolean;
};

export async function fetchInvite(token: string) {
  const response = await apiClient.get<{ ok: boolean; invite: InviteDetail }>(`/invites/${token}/`);
  return response.data;
}

export async function acceptInvite(token: string) {
  const response = await apiClient.post<{ ok: boolean; message: string }>(`/invites/${token}/accept/`);
  return response.data;
}
```

- [ ] **Step 3: Add coach-related functions to `frontend/src/api/coach.ts`**

Append to the end of the file:
```typescript
export type CoachJoinRequest = {
  id: number;
  athlete_name: string;
  athlete_username: string;
  created_at: string;
};

export async function fetchCoachCode() {
  const response = await apiClient.get<{ ok: boolean; coach_join_code: string }>("/coach/code/");
  return response.data;
}

export async function fetchCoachJoinRequests() {
  const response = await apiClient.get<{ ok: boolean; join_requests: CoachJoinRequest[] }>("/coach/join-requests/");
  return response.data;
}

export async function approveJoinRequest(requestId: number) {
  const response = await apiClient.post<{ ok: boolean; request_id: number }>(`/coach/join-requests/${requestId}/approve/`);
  return response.data;
}

export async function rejectJoinRequest(requestId: number) {
  const response = await apiClient.post<{ ok: boolean; request_id: number }>(`/coach/join-requests/${requestId}/reject/`);
  return response.data;
}

export async function requestCoachByCode(coachCode: string) {
  const response = await apiClient.post<{ ok: boolean; message: string }>("/coach/join-request/", {
    coach_code: coachCode,
  });
  return response.data;
}

export async function removeAthlete(athleteId: number, confirmName: string) {
  const response = await apiClient.delete<{ ok: boolean }>(`/coach/athletes/${athleteId}/`, {
    data: { confirm_name: confirmName },
  });
  return response.data;
}
```

- [ ] **Step 4: Add `garminWeekSync` to `frontend/src/api/imports.ts`**

Append to the end of the file:
```typescript
export async function garminWeekSync(weekStart: string) {
  const response = await apiClient.post<{ ok: boolean; replaced: number; untouched: number; message: string }>(
    "/imports/garmin/week-sync/",
    { week_start: weekStart },
  );
  return response.data;
}
```

- [ ] **Step 5: Extend TrainingRow type and add addNextMonth in `frontend/src/api/training.ts`**

In the `planned_metrics` block of `TrainingRow`, add:
```typescript
  planned_metrics: {
    planned_km_value: number;
    planned_km_text: string;
    planned_km_confidence: "high" | "medium" | "low";
    planned_km_show: boolean;
    planned_km_detail_km: string;
    planned_km_detail_reason: string;
    planned_km_detail_where: string;
  } | null;
```

Append to the end of the file:
```typescript
export async function addNextMonth(athleteId?: number) {
  const response = await apiClient.post<{ ok: boolean; month_created: boolean; weeks_created: number; days_created: number }>(
    "/training/months/",
    athleteId ? { athlete_id: athleteId } : {},
  );
  return response.data;
}
```

- [ ] **Step 6: Verify build**

```bash
cd /c/Users/admin/projects/enduroBuddy-personal/frontend && npm run build 2>&1 | tail -5
```
Expected: `✓ built in`

- [ ] **Step 7: Commit**

```bash
git add frontend/src/api/
git commit -m "feat(api): add legend, invites, coach code, week-sync, add-month API modules"
```

---

## Task 8: Frontend — Legend store

**Files:**
- Create: `frontend/src/stores/legend.ts`

- [ ] **Step 1: Create `frontend/src/stores/legend.ts`**

```typescript
import { ref } from "vue";
import { defineStore } from "pinia";
import { fetchLegend, saveLegend } from "@/api/legend";
import type { LegendState } from "@/api/legend";
import { useToastStore } from "@/stores/toasts";

export const useLegendStore = defineStore("legend", () => {
  const state = ref<LegendState>({});
  const isLoading = ref(false);
  const isSaving = ref(false);
  const isLoaded = ref(false);

  async function load() {
    if (isLoaded.value) return;
    isLoading.value = true;
    try {
      const data = await fetchLegend();
      state.value = data.state;
      isLoaded.value = true;
    } finally {
      isLoading.value = false;
    }
  }

  async function save(nextState: LegendState) {
    const toastStore = useToastStore();
    isSaving.value = true;
    try {
      const data = await saveLegend(nextState);
      state.value = data.state;
      toastStore.push("Legend saved.", "success");
    } catch (error) {
      toastStore.push(error instanceof Error ? error.message : "Could not save legend.", "danger");
      throw error;
    } finally {
      isSaving.value = false;
    }
  }

  return { state, isLoading, isSaving, isLoaded, load, save };
});
```

- [ ] **Step 2: Verify build**

```bash
cd /c/Users/admin/projects/enduroBuddy-personal/frontend && npm run build 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/stores/legend.ts
git commit -m "feat(store): add legend Pinia store"
```

---

## Task 9: Frontend — Locale strings

**Files:**
- Modify: `frontend/src/locales/cs.json`
- Modify: `frontend/src/locales/en.json`

- [ ] **Step 1: Add all new keys to `frontend/src/locales/cs.json`**

Add before the closing `}`:
```json
  "legend": {
    "button": "Legenda",
    "title": "Tréninková legenda",
    "zonesTitle": "Tepové zóny",
    "thresholdsTitle": "Prahy",
    "prsTitle": "Osobní rekordy",
    "zoneLabel": "Zóna {n}",
    "from": "Od (bpm)",
    "to": "Do (bpm)",
    "aerobic": "Aerobní práh",
    "anaerobic": "Anaerobní práh",
    "distance": "Vzdálenost",
    "time": "Čas",
    "addPr": "Přidat PR",
    "removePr": "Odebrat",
    "save": "Uložit",
    "saving": "Ukládám...",
    "close": "Zavřít",
    "linkedActivity": "Garmin"
  },
  "invite": {
    "loading": "Načítám pozvánku...",
    "title": "Pozvánka do tréninku",
    "group": "Skupina: {name}",
    "coach": "Trenér: {name}",
    "accept": "Přijmout pozvánku",
    "accepting": "Přijímám...",
    "accepted": "Pozvánka přijata!",
    "expired": "Tato pozvánka vypršela.",
    "used": "Tato pozvánka již byla použita.",
    "notFound": "Pozvánka nenalezena.",
    "error": "Nepodařilo se načíst pozvánku."
  },
  "addMonth": {
    "button": "Přidat měsíc",
    "adding": "Přidávám...",
    "created": "Nový měsíc přidán.",
    "extended": "Měsíc rozšířen.",
    "error": "Nepodařilo se přidat měsíc."
  },
  "requestCoach": {
    "title": "Požádat o trenéra",
    "codePlaceholder": "Kód trenéra (12 znaků)",
    "submit": "Odeslat žádost",
    "submitting": "Odesílám...",
    "success": "Žádost odeslána.",
    "error": "Nepodařilo se odeslat žádost."
  },
  "coachCode": {
    "label": "Kód trenéra",
    "copy": "Kopírovat",
    "copied": "Zkopírováno!"
  },
  "joinRequests": {
    "title": "Žádosti o trénování",
    "empty": "Žádné čekající žádosti.",
    "approve": "Schválit",
    "reject": "Zamítnout",
    "approving": "Schvaluji...",
    "rejecting": "Zamítám...",
    "approved": "Žádost schválena.",
    "rejected": "Žádost zamítnuta."
  },
  "removeAthlete": {
    "button": "Odebrat atleta",
    "confirmLabel": "Pro potvrzení opiš jméno atleta:",
    "confirm": "Odebrat",
    "confirming": "Odebírám...",
    "success": "Atlet odebrán.",
    "nameMismatch": "Jméno se neshoduje."
  },
  "weekCard": {
    "garminSync": "Sync Garmin",
    "garminSyncing": "Synchronizuji...",
    "garminSyncDone": "Synchronizováno."
  }
```

- [ ] **Step 2: Add all new keys to `frontend/src/locales/en.json`**

Add before the closing `}`:
```json
  "legend": {
    "button": "Legend",
    "title": "Training Legend",
    "zonesTitle": "Heart Rate Zones",
    "thresholdsTitle": "Thresholds",
    "prsTitle": "Personal Records",
    "zoneLabel": "Zone {n}",
    "from": "From (bpm)",
    "to": "To (bpm)",
    "aerobic": "Aerobic threshold",
    "anaerobic": "Anaerobic threshold",
    "distance": "Distance",
    "time": "Time",
    "addPr": "Add PR",
    "removePr": "Remove",
    "save": "Save",
    "saving": "Saving...",
    "close": "Close",
    "linkedActivity": "Garmin"
  },
  "invite": {
    "loading": "Loading invite...",
    "title": "Training Invite",
    "group": "Group: {name}",
    "coach": "Coach: {name}",
    "accept": "Accept invitation",
    "accepting": "Accepting...",
    "accepted": "Invitation accepted!",
    "expired": "This invitation has expired.",
    "used": "This invitation has already been used.",
    "notFound": "Invitation not found.",
    "error": "Could not load invitation."
  },
  "addMonth": {
    "button": "Add month",
    "adding": "Adding...",
    "created": "New month added.",
    "extended": "Month extended.",
    "error": "Could not add month."
  },
  "requestCoach": {
    "title": "Request a coach",
    "codePlaceholder": "Coach code (12 chars)",
    "submit": "Send request",
    "submitting": "Sending...",
    "success": "Request sent.",
    "error": "Could not send request."
  },
  "coachCode": {
    "label": "Coach code",
    "copy": "Copy",
    "copied": "Copied!"
  },
  "joinRequests": {
    "title": "Coaching requests",
    "empty": "No pending requests.",
    "approve": "Approve",
    "reject": "Reject",
    "approving": "Approving...",
    "rejecting": "Rejecting...",
    "approved": "Request approved.",
    "rejected": "Request rejected."
  },
  "removeAthlete": {
    "button": "Remove athlete",
    "confirmLabel": "Type the athlete's name to confirm:",
    "confirm": "Remove",
    "confirming": "Removing...",
    "success": "Athlete removed.",
    "nameMismatch": "Name does not match."
  },
  "weekCard": {
    "garminSync": "Sync Garmin",
    "garminSyncing": "Syncing...",
    "garminSyncDone": "Synced."
  }
```

**Note:** The `weekCard` key already exists in the locale files — merge the new keys into the existing object instead of creating a duplicate.

- [ ] **Step 3: Verify build**

```bash
cd /c/Users/admin/projects/enduroBuddy-personal/frontend && npm run build 2>&1 | tail -5
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/locales/
git commit -m "feat(i18n): add locale keys for legend, invite, add-month, coach requests"
```

---

## Task 10: Frontend — Linked activity lock in CompletedEditor + CompletedRow

**Files:**
- Modify: `frontend/src/components/training/CompletedEditor.vue`
- Modify: `frontend/src/components/training/CompletedRow.vue`

- [ ] **Step 1: Update `CompletedEditor.vue` to disable when has_linked_activity**

In `CompletedEditor.vue`, the `EbButton` for edit already checks `row.editable`. But when `has_linked_activity` is true, the edit button should be hidden entirely. Update the template's edit button condition:

Find:
```html
<EbButton v-if="row.editable" variant="ghost" @click="openEditor">{{ t("completedEditor.edit") }}</EbButton>
```

Replace with:
```html
<EbButton v-if="row.editable && !row.has_linked_activity" variant="ghost" @click="openEditor">{{ t("completedEditor.edit") }}</EbButton>
```

- [ ] **Step 2: Add linked-activity badge in `CompletedRow.vue`**

In `CompletedRow.vue`, find the `completed-row__meta` div and add the badge before `EbBadge`:
```html
<div class="completed-row__meta">
  <span v-if="row.has_linked_activity" class="completed-row__linked-badge">{{ t("legend.linkedActivity") }}</span>
  <div v-if="row.completed_metrics?.details" class="completed-row__details">
    {{ row.completed_metrics?.details }}
  </div>
  <div class="completed-row__hr">
    {{ t("completedRow.hr", { avg: row.completed_metrics?.avg_hr ?? "-", max: row.completed_metrics?.max_hr ?? "-" }) }}
  </div>
  <EbBadge :tone="row.status === 'done' ? 'done' : 'missed'">
    {{ row.status === "done" ? t("completedRow.done") : t("completedRow.missed") }}
  </EbBadge>
</div>
```

Add the `useI18n` import and call to `CompletedRow.vue` script:
```typescript
import { useI18n } from "@/composables/useI18n";
const { t } = useI18n();
```

Add to CompletedRow.vue `<style scoped>`:
```css
.completed-row__linked-badge {
  display: inline-flex;
  align-items: center;
  min-height: 1.375rem;
  padding: 0 0.5rem;
  border: 1px solid rgba(56, 189, 248, 0.22);
  border-radius: 999px;
  color: var(--eb-blue);
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
```

- [ ] **Step 3: Verify build and tests**

```bash
cd /c/Users/admin/projects/enduroBuddy-personal/frontend && npm run build 2>&1 | tail -5 && npm test -- --run 2>&1 | tail -10
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/training/CompletedEditor.vue frontend/src/components/training/CompletedRow.vue
git commit -m "feat(ui): lock completed editor when linked to Garmin activity"
```

---

## Task 11: Frontend — KM detail popover in PlannedRow

**Files:**
- Modify: `frontend/src/components/training/PlannedRow.vue`

- [ ] **Step 1: Add popover to PlannedRow.vue**

In `PlannedRow.vue`, find the `training-row__metrics` div:
```html
<div class="training-row__metrics" :class="confidenceClass">{{ metricsLabel }}</div>
```

Replace with:
```html
<div class="training-row__km-wrap">
  <div class="training-row__metrics" :class="confidenceClass">{{ metricsLabel }}</div>
  <div v-if="row.planned_metrics?.planned_km_show" class="training-row__km-popover">
    <div class="training-row__km-popover-inner">
      <div v-if="row.planned_metrics.planned_km_detail_km" class="training-row__km-popover-row">
        <span class="training-row__km-popover-label">km</span>
        <span>{{ row.planned_metrics.planned_km_detail_km }}</span>
      </div>
      <div v-if="row.planned_metrics.planned_km_detail_reason" class="training-row__km-popover-row">
        <span class="training-row__km-popover-label">source</span>
        <span>{{ row.planned_metrics.planned_km_detail_reason }}</span>
      </div>
      <div v-if="row.planned_metrics.planned_km_detail_where" class="training-row__km-popover-row">
        <span class="training-row__km-popover-label">where</span>
        <span>{{ row.planned_metrics.planned_km_detail_where }}</span>
      </div>
    </div>
  </div>
</div>
```

Add to PlannedRow.vue `<style scoped>`:
```css
.training-row__km-wrap {
  position: relative;
}

.training-row__km-wrap:hover .training-row__km-popover {
  opacity: 1;
  pointer-events: auto;
  transform: translateY(0);
}

.training-row__km-popover {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 20;
  min-width: 14rem;
  padding: 0.65rem 0.85rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-md);
  background: var(--eb-surface);
  box-shadow: var(--eb-shadow-soft);
  opacity: 0;
  pointer-events: none;
  transform: translateY(-4px);
  transition:
    opacity 150ms ease-out,
    transform 150ms ease-out;
}

.training-row__km-popover-inner {
  display: grid;
  gap: 0.35rem;
}

.training-row__km-popover-row {
  display: flex;
  gap: 0.5rem;
  align-items: baseline;
  font-family: var(--eb-font-mono);
  font-size: 0.75rem;
  color: var(--eb-text);
}

.training-row__km-popover-label {
  min-width: 3.5rem;
  color: var(--eb-text-muted);
  font-size: 0.625rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
```

- [ ] **Step 2: Verify build and tests**

```bash
cd /c/Users/admin/projects/enduroBuddy-personal/frontend && npm run build 2>&1 | tail -5 && npm test -- --run 2>&1 | tail -10
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/training/PlannedRow.vue
git commit -m "feat(ui): add planned KM detail popover"
```

---

## Task 12: Frontend — Garmin week sync button in WeekCard

**Files:**
- Modify: `frontend/src/components/training/WeekCard.vue`

- [ ] **Step 1: Add week sync button to WeekCard.vue**

In `WeekCard.vue`, add to the script setup:
```typescript
import { ref } from "vue";
import { garminWeekSync } from "@/api/imports";
import { useAuthStore } from "@/stores/auth";
import { useToastStore } from "@/stores/toasts";

const authStore = useAuthStore();
const toastStore = useToastStore();
const isSyncingGarmin = ref(false);

async function syncGarminWeek() {
  isSyncingGarmin.value = true;
  try {
    const result = await garminWeekSync(props.week.week_start);
    toastStore.push(result.message || t("weekCard.garminSyncDone"), "success");
  } catch (error) {
    toastStore.push(error instanceof Error ? error.message : t("weekCard.garminSyncDone"), "danger");
  } finally {
    isSyncingGarmin.value = false;
  }
}

const showGarminSync = computed(() => {
  return Boolean(
    authStore.user?.capabilities.has_garmin_connection &&
    authStore.user?.capabilities.garmin_sync_enabled &&
    props.week.has_started
  );
});
```

In the template, add the sync button inside `.week-card__header` on the right side, after `.week-card__stats`:
```html
<EbButton
  v-if="showGarminSync"
  variant="ghost"
  :disabled="isSyncingGarmin"
  @click="syncGarminWeek"
>
  {{ isSyncingGarmin ? t("weekCard.garminSyncing") : t("weekCard.garminSync") }}
</EbButton>
```

- [ ] **Step 2: Verify build and tests**

```bash
cd /c/Users/admin/projects/enduroBuddy-personal/frontend && npm run build 2>&1 | tail -5 && npm test -- --run 2>&1 | tail -10
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/training/WeekCard.vue
git commit -m "feat(ui): add Garmin week sync button to WeekCard"
```

---

## Task 13: Frontend — LegendModal component

**Files:**
- Create: `frontend/src/components/layout/LegendModal.vue`

- [ ] **Step 1: Create `frontend/src/components/layout/LegendModal.vue`**

```vue
<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { LegendState, LegendZone } from "@/api/legend";
import { PR_DISTANCES } from "@/api/legend";
import EbButton from "@/components/ui/EbButton.vue";
import EbModal from "@/components/ui/EbModal.vue";
import { useI18n } from "@/composables/useI18n";
import { useAuthStore } from "@/stores/auth";
import { useLegendStore } from "@/stores/legend";

const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{ close: [] }>();

const { t } = useI18n();
const authStore = useAuthStore();
const legendStore = useLegendStore();

const canEdit = computed(() => authStore.user?.role === "COACH");
const draft = ref<LegendState>({});
const newPrDistance = ref("");
const newPrTime = ref("");

watch(
  () => props.open,
  async (isOpen) => {
    if (isOpen) {
      await legendStore.load();
      draft.value = JSON.parse(JSON.stringify(legendStore.state));
    }
  },
);

const zones = computed(() => ["z1", "z2", "z3", "z4", "z5"] as const);

function getZone(key: string): LegendZone {
  return (draft.value.zones as Record<string, LegendZone>)?.[key] ?? { from: "", to: "" };
}

function setZoneField(key: string, field: "from" | "to", value: string) {
  if (!draft.value.zones) draft.value.zones = {};
  if (!(draft.value.zones as Record<string, LegendZone>)[key]) {
    (draft.value.zones as Record<string, LegendZone>)[key] = { from: "", to: "" };
  }
  (draft.value.zones as Record<string, LegendZone>)[key][field] = value;
}

function addPr() {
  if (!newPrDistance.value || !newPrTime.value) return;
  if (!draft.value.prs) draft.value.prs = [];
  const existing = draft.value.prs.findIndex((p) => p.distance === newPrDistance.value);
  if (existing >= 0) {
    draft.value.prs[existing].time = newPrTime.value;
  } else {
    draft.value.prs.push({ distance: newPrDistance.value, time: newPrTime.value });
  }
  newPrDistance.value = "";
  newPrTime.value = "";
}

function removePr(index: number) {
  draft.value.prs?.splice(index, 1);
}

async function save() {
  await legendStore.save(draft.value);
  emit("close");
}
</script>

<template>
  <EbModal :open="props.open" @close="emit('close')">
    <div class="legend-modal">
      <div class="legend-modal__header">
        <h2 class="legend-modal__title">{{ t("legend.title") }}</h2>
        <EbButton variant="ghost" @click="emit('close')">{{ t("legend.close") }}</EbButton>
      </div>

      <div v-if="legendStore.isLoading" class="legend-modal__loading">...</div>

      <template v-else>
        <!-- HR Zones -->
        <section class="legend-modal__section">
          <div class="legend-modal__section-label">{{ t("legend.zonesTitle") }}</div>
          <div class="legend-modal__zones">
            <div class="legend-modal__zone-head">
              <span></span>
              <span>{{ t("legend.from") }}</span>
              <span>{{ t("legend.to") }}</span>
            </div>
            <div v-for="zk in zones" :key="zk" class="legend-modal__zone-row">
              <span class="legend-modal__zone-name">{{ zk.toUpperCase() }}</span>
              <input
                v-if="canEdit"
                class="legend-modal__input"
                type="number"
                min="0"
                max="260"
                :value="getZone(zk).from"
                @input="setZoneField(zk, 'from', ($event.target as HTMLInputElement).value)"
              />
              <span v-else class="legend-modal__value">{{ getZone(zk).from || "—" }}</span>
              <input
                v-if="canEdit"
                class="legend-modal__input"
                type="number"
                min="0"
                max="260"
                :value="getZone(zk).to"
                @input="setZoneField(zk, 'to', ($event.target as HTMLInputElement).value)"
              />
              <span v-else class="legend-modal__value">{{ getZone(zk).to || "—" }}</span>
            </div>
          </div>
        </section>

        <!-- Thresholds -->
        <section class="legend-modal__section">
          <div class="legend-modal__section-label">{{ t("legend.thresholdsTitle") }}</div>
          <div class="legend-modal__thresholds">
            <label class="legend-modal__threshold-row">
              <span>{{ t("legend.aerobic") }}</span>
              <input v-if="canEdit" v-model="draft.aerobic_threshold" class="legend-modal__input" type="number" min="0" max="260" />
              <span v-else class="legend-modal__value">{{ draft.aerobic_threshold || "—" }}</span>
            </label>
            <label class="legend-modal__threshold-row">
              <span>{{ t("legend.anaerobic") }}</span>
              <input v-if="canEdit" v-model="draft.anaerobic_threshold" class="legend-modal__input" type="number" min="0" max="260" />
              <span v-else class="legend-modal__value">{{ draft.anaerobic_threshold || "—" }}</span>
            </label>
          </div>
        </section>

        <!-- PRs -->
        <section class="legend-modal__section">
          <div class="legend-modal__section-label">{{ t("legend.prsTitle") }}</div>
          <div class="legend-modal__prs">
            <div v-for="(pr, i) in (draft.prs || [])" :key="pr.distance" class="legend-modal__pr-row">
              <span class="legend-modal__pr-distance">{{ pr.distance }}</span>
              <span class="legend-modal__pr-time">{{ pr.time }}</span>
              <EbButton v-if="canEdit" variant="ghost" @click="removePr(i)">{{ t("legend.removePr") }}</EbButton>
            </div>
            <div v-if="canEdit" class="legend-modal__pr-add">
              <select v-model="newPrDistance" class="legend-modal__select">
                <option value="">{{ t("legend.distance") }}</option>
                <option v-for="d in PR_DISTANCES" :key="d" :value="d">{{ d }}</option>
              </select>
              <input v-model="newPrTime" class="legend-modal__input" type="text" :placeholder="t('legend.time')" maxlength="20" />
              <EbButton variant="secondary" :disabled="!newPrDistance || !newPrTime" @click="addPr">{{ t("legend.addPr") }}</EbButton>
            </div>
          </div>
        </section>

        <div v-if="canEdit" class="legend-modal__actions">
          <EbButton variant="ghost" @click="emit('close')">{{ t("legend.close") }}</EbButton>
          <EbButton :disabled="legendStore.isSaving" @click="save">
            {{ legendStore.isSaving ? t("legend.saving") : t("legend.save") }}
          </EbButton>
        </div>
      </template>
    </div>
  </EbModal>
</template>

<style scoped>
.legend-modal {
  width: min(90vw, 480px);
  max-height: 80vh;
  overflow-y: auto;
  display: grid;
  gap: 1.5rem;
  padding: 1.5rem;
}

.legend-modal__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.legend-modal__title {
  margin: 0;
  font-family: var(--eb-font-display);
  font-size: 1.25rem;
}

.legend-modal__loading {
  color: var(--eb-text-muted);
  font-size: 0.875rem;
}

.legend-modal__section {
  display: grid;
  gap: 0.75rem;
}

.legend-modal__section-label {
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.legend-modal__zones {
  display: grid;
  gap: 0.45rem;
}

.legend-modal__zone-head,
.legend-modal__zone-row {
  display: grid;
  grid-template-columns: 2.5rem 1fr 1fr;
  gap: 0.5rem;
  align-items: center;
}

.legend-modal__zone-head {
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.legend-modal__zone-name {
  color: var(--eb-lime);
  font-family: var(--eb-font-mono);
  font-size: 0.8125rem;
  font-weight: 700;
}

.legend-modal__thresholds {
  display: grid;
  gap: 0.65rem;
}

.legend-modal__threshold-row {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.875rem;
}

.legend-modal__input,
.legend-modal__select {
  width: 100%;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-sm);
  background: var(--eb-bg);
  color: var(--eb-text);
  padding: 0.5rem 0.65rem;
  font-family: var(--eb-font-mono);
  font-size: 0.875rem;
}

.legend-modal__input:focus,
.legend-modal__select:focus {
  outline: none;
  border-color: rgba(200, 255, 0, 0.4);
  box-shadow: var(--eb-glow-lime);
}

.legend-modal__value {
  font-family: var(--eb-font-mono);
  font-size: 0.875rem;
  color: var(--eb-text);
}

.legend-modal__prs {
  display: grid;
  gap: 0.5rem;
}

.legend-modal__pr-row {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 0.75rem;
  align-items: center;
}

.legend-modal__pr-distance {
  font-size: 0.875rem;
}

.legend-modal__pr-time {
  font-family: var(--eb-font-mono);
  font-size: 0.875rem;
  color: var(--eb-lime);
}

.legend-modal__pr-add {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 0.5rem;
  margin-top: 0.25rem;
}

.legend-modal__actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}
</style>
```

- [ ] **Step 2: Verify build**

```bash
cd /c/Users/admin/projects/enduroBuddy-personal/frontend && npm run build 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/layout/LegendModal.vue
git commit -m "feat(ui): add LegendModal component"
```

---

## Task 14: Frontend — Add legend button to TopNav

**Files:**
- Modify: `frontend/src/components/layout/TopNav.vue`

- [ ] **Step 1: Add legend button and modal to TopNav.vue**

In the script, add imports and state:
```typescript
import LegendModal from "@/components/layout/LegendModal.vue";
const isLegendOpen = ref(false);
```

In the template, add before `<NotificationBell />` in `.top-nav__actions`:
```html
<button class="top-nav__legend-btn" type="button" :title="t('legend.button')" @click="isLegendOpen = true">
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
    <rect x="1" y="3" width="14" height="2" rx="1" fill="currentColor" opacity="0.5"/>
    <rect x="1" y="7" width="9" height="2" rx="1" fill="currentColor"/>
    <rect x="1" y="11" width="11" height="2" rx="1" fill="currentColor" opacity="0.7"/>
  </svg>
</button>
<LegendModal :open="isLegendOpen" @close="isLegendOpen = false" />
```

Add to `.top-nav__actions` style (in `<style scoped>`):
```css
.top-nav__legend-btn {
  display: inline-grid;
  place-items: center;
  width: 2.25rem;
  height: 2.25rem;
  border: 0;
  border-radius: var(--eb-radius-md);
  background: transparent;
  color: var(--eb-text-soft);
  transition: background-color 150ms ease-out, color 150ms ease-out;
}

.top-nav__legend-btn:hover {
  background: var(--eb-surface-hover);
  color: var(--eb-text);
}
```

- [ ] **Step 2: Verify build and tests**

```bash
cd /c/Users/admin/projects/enduroBuddy-personal/frontend && npm run build 2>&1 | tail -5 && npm test -- --run 2>&1 | tail -10
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/layout/TopNav.vue
git commit -m "feat(ui): add legend button to TopNav"
```

---

## Task 15: Frontend — Add month buttons (AthleteView + CoachView)

**Files:**
- Modify: `frontend/src/views/dashboard/AthleteView.vue`
- Modify: `frontend/src/views/dashboard/CoachView.vue`

- [ ] **Step 1: Add month button to AthleteView.vue**

In `AthleteView.vue` script, add:
```typescript
import { ref } from "vue";
import { addNextMonth } from "@/api/training";
import { useToastStore } from "@/stores/toasts";
import EbButton from "@/components/ui/EbButton.vue";

const toastStore = useToastStore();
const isAddingMonth = ref(false);

async function addMonth() {
  isAddingMonth.value = true;
  try {
    const result = await addNextMonth();
    toastStore.push(result.month_created ? t("addMonth.created") : t("addMonth.extended"), "success");
    await trainingStore.loadDashboard();
  } catch (error) {
    toastStore.push(error instanceof Error ? error.message : t("addMonth.error"), "danger");
  } finally {
    isAddingMonth.value = false;
  }
}
```

In the template, after the `</template>` closing tag of the `v-else` block (after `</div>` that wraps `week-card` items), add:
```html
<div class="dashboard-view__add-month">
  <EbButton variant="ghost" :disabled="isAddingMonth" @click="addMonth">
    {{ isAddingMonth ? t("addMonth.adding") : t("addMonth.button") }}
  </EbButton>
</div>
```

Add to `<style scoped>`:
```css
.dashboard-view__add-month {
  display: flex;
  justify-content: center;
  padding: 0.5rem 0 1rem;
}
```

- [ ] **Step 2: Add month button to CoachView.vue**

In `CoachView.vue` script, add:
```typescript
import { addNextMonth } from "@/api/training";
const isAddingMonth = ref(false);

async function addMonth() {
  if (!coachStore.selectedAthlete) return;
  isAddingMonth.value = true;
  try {
    const result = await addNextMonth(coachStore.selectedAthlete.id);
    toastStore.push(result.month_created ? t("addMonth.created") : t("addMonth.extended"), "success");
    await coachStore.loadDashboard();
  } catch (error) {
    toastStore.push(error instanceof Error ? error.message : t("addMonth.error"), "danger");
  } finally {
    isAddingMonth.value = false;
  }
}
```

Also add `const toastStore = useToastStore();` and `import { useToastStore } from "@/stores/toasts";` if not already present.

In the template, after the `coach-view__weeks` div (at the end of the `v-else-if="coachStore.selectedAthlete"` block):
```html
<div class="coach-view__add-month">
  <EbButton variant="ghost" :disabled="isAddingMonth" @click="addMonth">
    {{ isAddingMonth ? t("addMonth.adding") : t("addMonth.button") }}
  </EbButton>
</div>
```

Add to `<style scoped>`:
```css
.coach-view__add-month {
  display: flex;
  justify-content: center;
  padding: 0.5rem 0 1rem;
}
```

- [ ] **Step 3: Verify build and tests**

```bash
cd /c/Users/admin/projects/enduroBuddy-personal/frontend && npm run build 2>&1 | tail -5 && npm test -- --run 2>&1 | tail -10
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/dashboard/AthleteView.vue frontend/src/views/dashboard/CoachView.vue
git commit -m "feat(ui): add month buttons to athlete and coach views"
```

---

## Task 16: Frontend — Coach code + join requests + remove athlete in AthleteManageModal

**Files:**
- Modify: `frontend/src/components/coach/AthleteManageModal.vue`

- [ ] **Step 1: Read the current AthleteManageModal.vue**

Before editing, read the file to understand current structure:
`frontend/src/components/coach/AthleteManageModal.vue`

- [ ] **Step 2: Extend AthleteManageModal with tabs and new features**

Replace the entire file content with the tabbed version. The component needs:
- Existing "Svěřenci" (Athletes) tab — current content unchanged
- New "Kód trenéra" tab — shows coach code with copy button
- New "Žádosti" tab — lists pending join requests with approve/reject

Add to script:
```typescript
import { ref, computed, onMounted, watch } from "vue";
import {
  fetchCoachCode,
  fetchCoachJoinRequests,
  approveJoinRequest,
  rejectJoinRequest,
  removeAthlete,
} from "@/api/coach";
import type { CoachJoinRequest } from "@/api/coach";

// New tab state
const activeTab = ref<"athletes" | "code" | "requests">("athletes");
const coachCode = ref("");
const isLoadingCode = ref(false);
const joinRequests = ref<CoachJoinRequest[]>([]);
const isLoadingRequests = ref(false);
const processingRequestId = ref<number | null>(null);
const removeConfirmName = ref("");
const removingAthleteId = ref<number | null>(null);
const isRemoving = ref(false);

async function loadCoachCode() {
  if (coachCode.value) return;
  isLoadingCode.value = true;
  try {
    const data = await fetchCoachCode();
    coachCode.value = data.coach_join_code;
  } finally {
    isLoadingCode.value = false;
  }
}

async function loadJoinRequests() {
  isLoadingRequests.value = true;
  try {
    const data = await fetchCoachJoinRequests();
    joinRequests.value = data.join_requests;
  } finally {
    isLoadingRequests.value = false;
  }
}

async function copyCode() {
  if (coachCode.value) {
    await navigator.clipboard.writeText(coachCode.value);
    toastStore.push(t("coachCode.copied"), "success");
  }
}

async function handleApprove(id: number) {
  processingRequestId.value = id;
  try {
    await approveJoinRequest(id);
    joinRequests.value = joinRequests.value.filter((r) => r.id !== id);
    toastStore.push(t("joinRequests.approved"), "success");
  } catch (error) {
    toastStore.push(error instanceof Error ? error.message : t("joinRequests.approved"), "danger");
  } finally {
    processingRequestId.value = null;
  }
}

async function handleReject(id: number) {
  processingRequestId.value = id;
  try {
    await rejectJoinRequest(id);
    joinRequests.value = joinRequests.value.filter((r) => r.id !== id);
    toastStore.push(t("joinRequests.rejected"), "success");
  } catch (error) {
    toastStore.push(error instanceof Error ? error.message : t("joinRequests.rejected"), "danger");
  } finally {
    processingRequestId.value = null;
  }
}

function startRemoveAthlete(athleteId: number) {
  removingAthleteId.value = athleteId;
  removeConfirmName.value = "";
}

function cancelRemoveAthlete() {
  removingAthleteId.value = null;
  removeConfirmName.value = "";
}

async function confirmRemoveAthlete() {
  if (!removingAthleteId.value) return;
  isRemoving.value = true;
  try {
    await removeAthlete(removingAthleteId.value, removeConfirmName.value);
    toastStore.push(t("removeAthlete.success"), "success");
    emit("close");
  } catch (error) {
    toastStore.push(error instanceof Error ? error.message : t("removeAthlete.nameMismatch"), "danger");
  } finally {
    isRemoving.value = false;
    removingAthleteId.value = null;
    removeConfirmName.value = "";
  }
}

watch(activeTab, (tab) => {
  if (tab === "code") void loadCoachCode();
  if (tab === "requests") void loadJoinRequests();
});
```

Add tabs to the template before the existing athlete list:
```html
<div class="manage-tabs">
  <button
    class="manage-tabs__tab"
    :class="{ 'manage-tabs__tab--active': activeTab === 'athletes' }"
    type="button"
    @click="activeTab = 'athletes'"
  >{{ t("coachManage.title") }}</button>
  <button
    class="manage-tabs__tab"
    :class="{ 'manage-tabs__tab--active': activeTab === 'code' }"
    type="button"
    @click="activeTab = 'code'"
  >{{ t("coachCode.label") }}</button>
  <button
    class="manage-tabs__tab"
    :class="{ 'manage-tabs__tab--active': activeTab === 'requests' }"
    type="button"
    @click="activeTab = 'requests'"
  >{{ t("joinRequests.title") }}</button>
</div>
```

Wrap existing athlete list in `<div v-if="activeTab === 'athletes'">...</div>`.

Add code tab content:
```html
<div v-if="activeTab === 'code'" class="manage-code">
  <div class="manage-code__label">{{ t("coachCode.label") }}</div>
  <div v-if="isLoadingCode" class="manage-code__loading">...</div>
  <div v-else class="manage-code__row">
    <code class="manage-code__value">{{ coachCode }}</code>
    <EbButton variant="secondary" @click="copyCode">{{ t("coachCode.copy") }}</EbButton>
  </div>
</div>
```

Add requests tab content:
```html
<div v-if="activeTab === 'requests'" class="manage-requests">
  <div v-if="isLoadingRequests" class="manage-requests__loading">...</div>
  <div v-else-if="joinRequests.length === 0" class="manage-requests__empty">{{ t("joinRequests.empty") }}</div>
  <div v-else class="manage-requests__list">
    <div v-for="jr in joinRequests" :key="jr.id" class="manage-requests__row">
      <div class="manage-requests__name">{{ jr.athlete_name }}</div>
      <div class="manage-requests__username">@{{ jr.athlete_username }}</div>
      <div class="manage-requests__actions">
        <EbButton
          variant="secondary"
          :disabled="processingRequestId === jr.id"
          @click="handleApprove(jr.id)"
        >{{ t("joinRequests.approve") }}</EbButton>
        <EbButton
          variant="ghost"
          :disabled="processingRequestId === jr.id"
          @click="handleReject(jr.id)"
        >{{ t("joinRequests.reject") }}</EbButton>
      </div>
    </div>
  </div>
</div>
```

Add remove-athlete section inside the athletes tab (below the athlete list, before save button):
```html
<template v-if="removingAthleteId">
  <div class="manage-remove">
    <div class="manage-remove__label">{{ t("removeAthlete.confirmLabel") }}</div>
    <input v-model="removeConfirmName" class="manage-remove__input" type="text" />
    <div class="manage-remove__actions">
      <EbButton variant="ghost" :disabled="isRemoving" @click="cancelRemoveAthlete">{{ t("coachManage.cancel") }}</EbButton>
      <EbButton variant="danger" :disabled="isRemoving || !removeConfirmName" @click="confirmRemoveAthlete">
        {{ isRemoving ? t("removeAthlete.confirming") : t("removeAthlete.confirm") }}
      </EbButton>
    </div>
  </div>
</template>
```

Add "Remove athlete" button to each athlete row (inside the athlete loop, after the hide/show button):
```html
<EbButton
  v-if="!athlete.selected"
  variant="ghost"
  @click="startRemoveAthlete(athlete.id)"
>{{ t("removeAthlete.button") }}</EbButton>
```

Add tab + code + requests styles to `<style scoped>`:
```css
.manage-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--eb-border);
  margin-bottom: 1rem;
}

.manage-tabs__tab {
  padding: 0.65rem 1rem;
  border: 0;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--eb-text-muted);
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  transition: color 150ms ease-out;
}

.manage-tabs__tab--active {
  color: var(--eb-text);
  border-bottom-color: var(--eb-lime);
}

.manage-tabs__tab:hover:not(.manage-tabs__tab--active) {
  color: var(--eb-text-soft);
}

.manage-code {
  display: grid;
  gap: 0.75rem;
  padding: 0.5rem 0;
}

.manage-code__label {
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.manage-code__row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.manage-code__value {
  font-family: var(--eb-font-mono);
  font-size: 1.1rem;
  letter-spacing: 0.12em;
  color: var(--eb-lime);
  background: rgba(200, 255, 0, 0.06);
  padding: 0.5rem 1rem;
  border-radius: var(--eb-radius-sm);
  border: 1px solid rgba(200, 255, 0, 0.18);
}

.manage-requests__list {
  display: grid;
  gap: 0.75rem;
}

.manage-requests__row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.5rem 1rem;
  align-items: center;
  padding: 0.75rem 1rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-md);
  background: var(--eb-surface);
}

.manage-requests__name {
  font-size: 0.9375rem;
  font-weight: 500;
}

.manage-requests__username {
  grid-column: 1;
  color: var(--eb-text-muted);
  font-size: 0.8125rem;
}

.manage-requests__actions {
  grid-row: 1 / 3;
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.manage-requests__empty,
.manage-requests__loading {
  color: var(--eb-text-muted);
  font-size: 0.875rem;
  padding: 1rem 0;
}

.manage-remove {
  display: grid;
  gap: 0.65rem;
  padding: 1rem;
  border: 1px solid rgba(244, 63, 94, 0.25);
  border-radius: var(--eb-radius-md);
  background: rgba(244, 63, 94, 0.04);
  margin-top: 0.5rem;
}

.manage-remove__label {
  color: var(--eb-text-soft);
  font-size: 0.8125rem;
}

.manage-remove__input {
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-sm);
  background: var(--eb-bg);
  color: var(--eb-text);
  padding: 0.6rem 0.75rem;
}

.manage-remove__actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}
```

- [ ] **Step 3: Verify build and tests**

```bash
cd /c/Users/admin/projects/enduroBuddy-personal/frontend && npm run build 2>&1 | tail -5 && npm test -- --run 2>&1 | tail -10
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/coach/AthleteManageModal.vue
git commit -m "feat(ui): add code, requests, and remove-athlete tabs to AthleteManageModal"
```

---

## Task 17: Frontend — Request coach widget in AthleteView

**Files:**
- Modify: `frontend/src/views/dashboard/AthleteView.vue`

- [ ] **Step 1: Add request-coach widget to AthleteView.vue**

Add to script:
```typescript
import { requestCoachByCode } from "@/api/coach";
const coachCodeInput = ref("");
const isRequestingCoach = ref(false);

async function submitCoachRequest() {
  if (!coachCodeInput.value.trim()) return;
  isRequestingCoach.value = true;
  try {
    await requestCoachByCode(coachCodeInput.value.trim().toUpperCase());
    toastStore.push(t("requestCoach.success"), "success");
    coachCodeInput.value = "";
  } catch (error) {
    toastStore.push(error instanceof Error ? error.message : t("requestCoach.error"), "danger");
  } finally {
    isRequestingCoach.value = false;
  }
}
```

Add `const toastStore = useToastStore();` and `import { useToastStore } from "@/stores/toasts";` if not already present.

Add to the toolbar section (inside `.dashboard-view__toolbar`, alongside GarminImportModal):
```html
<div class="dashboard-view__request-coach">
  <input
    v-model="coachCodeInput"
    class="dashboard-view__coach-input"
    type="text"
    maxlength="12"
    :placeholder="t('requestCoach.codePlaceholder')"
    :disabled="isRequestingCoach"
    @keyup.enter="submitCoachRequest"
  />
  <EbButton variant="ghost" :disabled="isRequestingCoach || !coachCodeInput.trim()" @click="submitCoachRequest">
    {{ isRequestingCoach ? t("requestCoach.submitting") : t("requestCoach.submit") }}
  </EbButton>
</div>
```

Add to `<style scoped>`:
```css
.dashboard-view__toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.dashboard-view__request-coach {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.dashboard-view__coach-input {
  width: 10rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-sm);
  background: var(--eb-bg);
  color: var(--eb-text);
  padding: 0.5rem 0.65rem;
  font-family: var(--eb-font-mono);
  font-size: 0.875rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.dashboard-view__coach-input:focus {
  outline: none;
  border-color: rgba(56, 189, 248, 0.4);
  box-shadow: var(--eb-glow-blue);
}
```

- [ ] **Step 2: Verify build and tests**

```bash
cd /c/Users/admin/projects/enduroBuddy-personal/frontend && npm run build 2>&1 | tail -5 && npm test -- --run 2>&1 | tail -10
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/dashboard/AthleteView.vue
git commit -m "feat(ui): add request-coach code widget to athlete dashboard"
```

---

## Task 18: Frontend — Training group invite view

**Files:**
- Create: `frontend/src/views/invite/InviteView.vue`
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: Create `frontend/src/views/invite/InviteView.vue`**

```vue
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { acceptInvite, fetchInvite } from "@/api/invites";
import type { InviteDetail } from "@/api/invites";
import EbButton from "@/components/ui/EbButton.vue";
import EbCard from "@/components/ui/EbCard.vue";
import EbSpinner from "@/components/ui/EbSpinner.vue";
import AppShell from "@/components/layout/AppShell.vue";
import { useI18n } from "@/composables/useI18n";

const route = useRoute();
const router = useRouter();
const { t } = useI18n();
const token = route.params.token as string;

const isLoading = ref(true);
const isAccepting = ref(false);
const accepted = ref(false);
const errorMessage = ref("");
const invite = ref<InviteDetail | null>(null);

onMounted(async () => {
  try {
    const data = await fetchInvite(token);
    invite.value = data.invite;
  } catch {
    errorMessage.value = t("invite.notFound");
  } finally {
    isLoading.value = false;
  }
});

async function accept() {
  isAccepting.value = true;
  try {
    await acceptInvite(token);
    accepted.value = true;
    setTimeout(() => void router.push("/app/dashboard"), 2000);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t("invite.error");
  } finally {
    isAccepting.value = false;
  }
}
</script>

<template>
  <AppShell variant="athlete">
    <div class="invite-view">
      <EbCard class="invite-card">
        <div v-if="isLoading" class="invite-card__loading">
          <EbSpinner />
          <span>{{ t("invite.loading") }}</span>
        </div>

        <template v-else>
          <h1 class="invite-card__title">{{ t("invite.title") }}</h1>

          <div v-if="errorMessage" class="invite-card__error">{{ errorMessage }}</div>

          <template v-else-if="invite">
            <div v-if="accepted" class="invite-card__accepted">{{ t("invite.accepted") }}</div>

            <template v-else-if="invite.is_used">
              <p class="invite-card__message">{{ t("invite.used") }}</p>
            </template>

            <template v-else-if="invite.is_expired">
              <p class="invite-card__message">{{ t("invite.expired") }}</p>
            </template>

            <template v-else>
              <p class="invite-card__detail">{{ t("invite.group", { name: invite.group_name }) }}</p>
              <p class="invite-card__detail">{{ t("invite.coach", { name: invite.coach_name }) }}</p>
              <EbButton :disabled="isAccepting" @click="accept">
                {{ isAccepting ? t("invite.accepting") : t("invite.accept") }}
              </EbButton>
            </template>
          </template>
        </template>
      </EbCard>
    </div>
  </AppShell>
</template>

<style scoped>
.invite-view {
  display: grid;
  place-items: center;
  min-height: calc(100vh - var(--eb-topnav-height) - 4rem);
}

.invite-card {
  width: min(90vw, 400px);
  padding: 2rem;
  display: grid;
  gap: 1rem;
}

.invite-card__title {
  margin: 0;
  font-family: var(--eb-font-display);
  font-size: 1.5rem;
}

.invite-card__loading {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--eb-text-soft);
}

.invite-card__detail {
  margin: 0;
  color: var(--eb-text-soft);
  font-size: 0.9375rem;
}

.invite-card__error,
.invite-card__message {
  margin: 0;
  color: var(--eb-text-soft);
  font-size: 0.9375rem;
}

.invite-card__error {
  color: var(--eb-danger);
}

.invite-card__accepted {
  color: var(--eb-lime);
  font-weight: 600;
}
</style>
```

- [ ] **Step 2: Add route to `frontend/src/router/index.ts`**

Add to `routes` array:
```typescript
{
  path: "/coach/invite/:token",
  name: "invite-accept",
  component: () => import("@/views/invite/InviteView.vue"),
  meta: { appVariant: "athlete" },
},
```

- [ ] **Step 3: Verify build and tests**

```bash
cd /c/Users/admin/projects/enduroBuddy-personal/frontend && npm run build 2>&1 | tail -5 && npm test -- --run 2>&1 | tail -10
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/invite/InviteView.vue frontend/src/router/index.ts
git commit -m "feat(ui): add training group invite accept view"
```

---

## Self-Review Checklist

| Spec requirement | Task |
|---|---|
| Legend GET + POST endpoint | Task 1 |
| Garmin week sync endpoint | Task 2 |
| Add next month endpoint | Task 3 |
| Coach code endpoint | Task 4 |
| Join requests list + approve/reject | Task 4 |
| Athlete request coach by code | Task 4 |
| Remove athlete with confirm | Task 4 |
| Invite GET + accept endpoints | Task 5 |
| KM detail fields in dashboard response | Task 6 |
| API TypeScript modules | Task 7 |
| Legend Pinia store | Task 8 |
| Locale strings | Task 9 |
| Linked activity lock (CompletedEditor + badge) | Task 10 |
| KM detail popover (PlannedRow) | Task 11 |
| Garmin week sync button (WeekCard) | Task 12 |
| LegendModal component | Task 13 |
| Legend button in TopNav | Task 14 |
| Add month buttons (AthleteView + CoachView) | Task 15 |
| Code + requests + remove tabs in AthleteManageModal | Task 16 |
| Request-coach widget in AthleteView | Task 17 |
| Training group invite view + route | Task 18 |

All spec requirements covered. No placeholders. Types defined before use.
