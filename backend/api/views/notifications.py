import json

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from accounts.models import AppNotification
from accounts.services.notifications import mark_notifications_read, serialize_notification


@login_required
@require_GET
def list_notifications(request):
    notifications_qs = AppNotification.objects.filter(recipient=request.user)
    notifications_qs = notifications_qs.exclude(
        Q(dedupe_key__startswith="test-live-") | Q(text__startswith="Test live:")
    )
    notifications = list(
        notifications_qs.select_related("actor").order_by("-created_at", "-id")[:20]
    )
    unread_count = sum(1 for notification in notifications if notification.read_at is None)
    return JsonResponse(
        {
            "ok": True,
            "notifications": [serialize_notification(notification) for notification in notifications],
            "unread_count": unread_count,
        }
    )


@login_required
@require_POST
def mark_notifications_read_view(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)

    notification_ids = payload.get("notification_ids")
    if not isinstance(notification_ids, list):
        return JsonResponse({"ok": False, "error": "notification_ids must be a list."}, status=400)

    marked_count = mark_notifications_read(recipient=request.user, notification_ids=notification_ids)
    return JsonResponse({"ok": True, "marked_count": marked_count})
