from __future__ import annotations

from django.utils import timezone

from accounts.models import AppNotification, CoachJoinRequest
from training.models import PlannedTraining


def upsert_app_notification(*, recipient, kind: str, text: str, tone: str = "info", actor=None, dedupe_key: str = "") -> AppNotification:
    normalized_key = (dedupe_key or "").strip()
    if normalized_key:
        notification = (
            AppNotification.objects.filter(recipient=recipient, dedupe_key=normalized_key, read_at__isnull=True)
            .order_by("-id")
            .first()
        )
        if notification is not None:
            notification.text = text[:255]
            notification.tone = tone
            notification.actor = actor
            notification.save(update_fields=["text", "tone", "actor", "updated_at"])
            return notification

    return AppNotification.objects.create(
        recipient=recipient,
        actor=actor,
        kind=kind,
        tone=tone,
        text=text[:255],
        dedupe_key=normalized_key,
    )


def notify_new_coach_join_request(*, join_request: CoachJoinRequest) -> AppNotification:
    return upsert_app_notification(
        recipient=join_request.coach,
        actor=join_request.athlete,
        kind=AppNotification.Kind.COACH_JOIN_REQUEST,
        tone=AppNotification.Tone.INFO,
        text=f"Nová žádost o trénování od {join_request.athlete.username}.",
        dedupe_key=f"coach-join-request:{join_request.id}",
    )


def notify_athlete_plan_updated(*, planned: PlannedTraining, actor, field: str, old_value: str, new_value: str) -> AppNotification | None:
    athlete = getattr(planned.week.training_month, "athlete", None)
    if athlete is None or actor is None or athlete.id == actor.id:
        return None

    old_text = str(old_value or "").strip()
    new_text = str(new_value or "").strip()
    if old_text == new_text:
        return None

    date_label = f"{planned.date.day}. {planned.date.month}. {planned.date.year}" if planned.date else planned.day_label
    plan_label = new_text or planned.title or "trénink"

    if field == "notes":
        if not new_text:
            return None
        text = f"Trenér přidal poznámku k tréninku na {date_label}."
        kind = AppNotification.Kind.COACH_NOTE
        dedupe_key = f"coach-note:{planned.id}"
    else:
        if field == "title" and not old_text and new_text:
            text = f"Trenér přidal nový plán na {date_label}: {plan_label[:80]}."
        else:
            text = f"Trenér upravil plán na {date_label}: {plan_label[:80]}."
        kind = AppNotification.Kind.PLAN_UPDATED
        dedupe_key = f"plan-updated:{planned.id}:{field}"

    return upsert_app_notification(
        recipient=athlete,
        actor=actor,
        kind=kind,
        tone=AppNotification.Tone.INFO,
        text=text,
        dedupe_key=dedupe_key,
    )


def serialize_notification(notification: AppNotification) -> dict[str, object]:
    return {
        "id": notification.id,
        "kind": notification.kind,
        "tone": notification.tone,
        "text": notification.text,
        "actor": getattr(notification.actor, "username", ""),
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
        "read_at": notification.read_at.isoformat() if notification.read_at else None,
        "unread": notification.read_at is None,
    }


def mark_notifications_read(*, recipient, notification_ids: list[int]) -> int:
    ids = [int(notification_id) for notification_id in notification_ids if str(notification_id).isdigit()]
    if not ids:
        return 0
    return AppNotification.objects.filter(recipient=recipient, id__in=ids, read_at__isnull=True).update(read_at=timezone.now())
