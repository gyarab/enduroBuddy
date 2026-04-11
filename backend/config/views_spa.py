from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


def _render_spa(request):
    return render(
        request,
        "spa.html",
        {
            "debug": settings.DEBUG,
            "spa_vite_dev_server_url": getattr(settings, "SPA_VITE_DEV_SERVER_URL", "http://localhost:5173"),
            "spa_entry_css": "spa/app.css",
            "spa_entry_js": "spa/app.js",
        },
    )


@ensure_csrf_cookie
@login_required
def spa_entry(request, path: str | None = None):
    return _render_spa(request)


@ensure_csrf_cookie
def public_spa_entry(request, path: str | None = None):
    return _render_spa(request)
