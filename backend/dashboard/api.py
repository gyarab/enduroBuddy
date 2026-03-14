from __future__ import annotations

from django.http import JsonResponse


def json_error(message: str, *, status: int) -> JsonResponse:
    return JsonResponse({"ok": False, "error": message}, status=status)
