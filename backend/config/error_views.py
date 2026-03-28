from __future__ import annotations

from django.conf import settings
from django.http import Http404
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET


def bad_request(request: HttpRequest, exception) -> HttpResponse:
    return render(request, "400.html", status=400)


def permission_denied(request: HttpRequest, exception) -> HttpResponse:
    return render(request, "403.html", status=403)


def page_not_found(request: HttpRequest, exception) -> HttpResponse:
    return render(request, "404.html", status=404)


def server_error(request: HttpRequest) -> HttpResponse:
    return render(request, "500.html", status=500)


@require_GET
def error_preview_index(request: HttpRequest) -> HttpResponse:
    if not settings.DEBUG:
        raise Http404()
    previews = [
        {
            "label": "Preview 400",
            "url": "/__debug/ui/errors/400/",
            "description": "Bad request fallback page.",
            "real_case": "Malformed request, invalid payload, or explicit 400 response outside AJAX.",
        },
        {
            "label": "Preview 403",
            "url": "/__debug/ui/errors/403/",
            "description": "Permission denied fallback page.",
            "real_case": "User opens a forbidden page or a view raises PermissionDenied.",
        },
        {
            "label": "Preview 404",
            "url": "/__debug/ui/errors/404/",
            "description": "Not found fallback page.",
            "real_case": "Bad URL or missing resource page.",
        },
        {
            "label": "Preview 500",
            "url": "/__debug/ui/errors/500/",
            "description": "Internal server error fallback page.",
            "real_case": "Unhandled exception in production with DEBUG=False.",
        },
    ]
    account_pages = [
        {
            "label": "Account Inactive",
            "url": "/accounts/inactive/",
            "real_case": "Inactive or disabled account flow.",
        },
        {
            "label": "Manage Email",
            "url": "/accounts/email/",
            "real_case": "Direct account email management page.",
        },
        {
            "label": "Change Password",
            "url": "/accounts/password/change/",
            "real_case": "Direct password change route.",
        },
        {
            "label": "Set Password",
            "url": "/accounts/password/set/",
            "real_case": "Account without local password sets one.",
        },
        {
            "label": "Reauthenticate",
            "url": "/accounts/reauthenticate/",
            "real_case": "Sensitive action requires password confirmation.",
        },
        {
            "label": "Social Login Error",
            "url": "/accounts/social/login/error/",
            "real_case": "Google or other provider login flow fails.",
        },
        {
            "label": "Social Login Cancelled",
            "url": "/accounts/social/login/cancelled/",
            "real_case": "User cancels Google login/consent.",
        },
        {
            "label": "Social Connections",
            "url": "/accounts/social/connections/",
            "real_case": "Direct page for connected third-party accounts.",
        },
    ]
    return render(
        request,
        "debug/error_preview.html",
        {
            "previews": previews,
            "account_pages": account_pages,
            "debug_enabled": settings.DEBUG,
        },
    )


@require_GET
def error_preview_status(request: HttpRequest, status_code: int) -> HttpResponse:
    if not settings.DEBUG:
        raise Http404()
    template_name = f"{status_code}.html"
    titles = {
        400: "Neplatný požadavek",
        403: "Přístup zamítnut",
        404: "Stránka nenalezena",
        500: "Něco se pokazilo",
    }
    if status_code not in titles:
        return render(request, "404.html", status=404)
    return render(
        request,
        template_name,
        {
            "debug_preview": True,
            "preview_status_code": status_code,
        },
        status=status_code,
    )
