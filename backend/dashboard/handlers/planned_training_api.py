from __future__ import annotations

import json
from decimal import Decimal

from dashboard.api import json_error
from dashboard.services.planned_km import estimate_running_km_from_title
from dashboard.texts import ApiText
from training.models import PlannedTraining


MAX_PLANNED_DISTANCE_KM = Decimal("999.99")
PLANNED_UPDATE_FIELDS = {"title", "notes", "session_type"}
COMPLETED_UPDATE_FIELDS = {"km", "min", "third", "avg_hr", "max_hr"}


def parse_json_body(request):
    try:
        return json.loads(request.body.decode("utf-8")), None
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, json_error(ApiText.INVALID_JSON_BODY, status=400)


def validate_planned_update_payload(payload):
    planned_id = payload.get("planned_id")
    field = payload.get("field")
    value = payload.get("value", "")

    if not isinstance(planned_id, int):
        return None, json_error(ApiText.INVALID_PLANNED_ID, status=400)
    if field not in PLANNED_UPDATE_FIELDS:
        return None, json_error(ApiText.INVALID_FIELD, status=400)
    if not isinstance(value, str):
        return None, json_error(ApiText.INVALID_VALUE, status=400)
    if field == "session_type" and value not in {
        PlannedTraining.SessionType.RUN,
        PlannedTraining.SessionType.WORKOUT,
    }:
        return None, json_error(ApiText.INVALID_SESSION_TYPE, status=400)
    return (planned_id, field, value), None


def validate_completed_update_payload(payload):
    planned_id = payload.get("planned_id")
    field = payload.get("field")
    value = payload.get("value", "")

    if not isinstance(planned_id, int):
        return None, json_error(ApiText.INVALID_PLANNED_ID, status=400)
    if field not in COMPLETED_UPDATE_FIELDS:
        return None, json_error(ApiText.INVALID_FIELD, status=400)
    return (planned_id, field, value), None


def validate_planned_id_payload(payload):
    planned_id = payload.get("planned_id")
    if not isinstance(planned_id, int):
        return None, json_error(ApiText.INVALID_PLANNED_ID, status=400)
    return planned_id, None


def load_planned_training(planned_id: int, *, include_activity: bool = False):
    select_related = ["week__training_month"]
    if include_activity:
        select_related.append("activity")
    planned = PlannedTraining.objects.select_related(*select_related).filter(id=planned_id).first()
    if planned is None:
        return None, json_error(ApiText.PLANNED_TRAINING_NOT_FOUND, status=404)
    return planned, None


def planned_athlete_id(planned: PlannedTraining) -> int:
    return planned.week.training_month.athlete_id


def save_planned_field(*, planned: PlannedTraining, field: str, value: str):
    setattr(planned, field, value)
    update_fields = [field]
    if field == "title":
        estimated = estimate_running_km_from_title(value)
        if estimated is not None:
            estimated = min(estimated, MAX_PLANNED_DISTANCE_KM)
        planned.planned_distance_km = estimated
        update_fields.append("planned_distance_km")
    planned.save(update_fields=update_fields)
    return value
