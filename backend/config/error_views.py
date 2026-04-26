from __future__ import annotations

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_GET

_TITLES = {
    400: ("Neplatný požadavek", "Požadavek se nepodařilo zpracovat. Zkus stránku obnovit nebo akci zopakovat."),
    403: ("Přístup zamítnut", "Nemáš oprávnění zobrazit tuto stránku."),
    404: ("Stránka nenalezena", "Tahle adresa už neexistuje, nebo nikdy neexistovala."),
    500: ("Něco se pokazilo", "Na serveru nastala neočekávaná chyba. Zkus to znovu za chvíli."),
}

_HTML = """\
<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | EnduroBuddy</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#09090b;color:#fafafa;font-family:Inter,system-ui,sans-serif;
  min-height:100vh;display:flex;align-items:center;justify-content:center;padding:1rem}}
.card{{background:#18181b;border:1px solid #27272a;border-radius:16px;
  padding:2.5rem 2rem;max-width:28rem;width:100%;text-align:center}}
.code{{font-family:'JetBrains Mono',monospace;font-size:3rem;font-weight:700;
  color:#c8ff00;line-height:1;margin-bottom:1rem}}
h1{{font-size:1.25rem;font-weight:700;margin-bottom:.75rem}}
p{{color:#71717a;font-size:.9rem;line-height:1.6;margin-bottom:1.5rem}}
a{{display:inline-block;background:#c8ff00;color:#09090b;font-weight:600;
  font-size:.875rem;padding:.6rem 1.4rem;border-radius:8px;text-decoration:none}}
a:hover{{opacity:.9}}
</style>
</head>
<body>
<div class="card">
  <div class="code">{code}</div>
  <h1>{title}</h1>
  <p>{message}</p>
  <a href="/">Zpět na hlavní stránku</a>
</div>
</body>
</html>"""


def _is_api(request: HttpRequest) -> bool:
    return request.path.startswith("/api/")


def _html(code: int) -> HttpResponse:
    title, message = _TITLES[code]
    return HttpResponse(
        _HTML.format(code=code, title=title, message=message),
        status=code,
        content_type="text/html; charset=utf-8",
    )


def _json(code: int) -> JsonResponse:
    title, _ = _TITLES[code]
    return JsonResponse({"error": title, "status": code}, status=code)


def bad_request(request: HttpRequest, exception) -> HttpResponse:
    return _json(400) if _is_api(request) else _html(400)


def permission_denied(request: HttpRequest, exception) -> HttpResponse:
    return _json(403) if _is_api(request) else _html(403)


def page_not_found(request: HttpRequest, exception) -> HttpResponse:
    return _json(404) if _is_api(request) else _html(404)


def server_error(request: HttpRequest) -> HttpResponse:
    return _json(500) if _is_api(request) else _html(500)


# ── debug preview ─────────────────────────────────────────────────────────────

_PREVIEW_HTML = """\
<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="utf-8">
<title>Error UI Preview | EnduroBuddy</title>
<style>
body{{font-family:Inter,system-ui,sans-serif;background:#09090b;color:#fafafa;
  padding:2rem;max-width:56rem;margin:0 auto}}
h1{{font-size:1.4rem;font-weight:700;margin-bottom:1.5rem;color:#c8ff00}}
h2{{font-size:1rem;font-weight:600;margin:1.5rem 0 .75rem;color:#71717a;
  text-transform:uppercase;letter-spacing:.08em}}
ul{{list-style:none;display:grid;gap:.5rem}}
a{{color:#38bdf8;text-decoration:none}}a:hover{{text-decoration:underline}}
.desc{{color:#71717a;font-size:.85rem}}
</style>
</head>
<body>
<h1>UI fallback preview</h1>
<h2>Error pages</h2>
<ul>{preview_items}</ul>
<h2>Account pages</h2>
<ul>{account_items}</ul>
</body>
</html>"""


@require_GET
def error_preview_index(request: HttpRequest) -> HttpResponse:
    if not settings.DEBUG:
        raise Http404()

    previews = [
        ("Preview 400", "/__debug/ui/errors/400/", "Malformed request or explicit 400 outside AJAX."),
        ("Preview 403", "/__debug/ui/errors/403/", "User opens a forbidden page."),
        ("Preview 404", "/__debug/ui/errors/404/", "Bad URL or missing resource."),
        ("Preview 500", "/__debug/ui/errors/500/", "Unhandled exception in production."),
    ]
    account_pages = [
        ("Account Inactive", "/accounts/inactive/"),
        ("Manage Email", "/accounts/email/"),
        ("Change Password", "/accounts/password/change/"),
        ("Set Password", "/accounts/password/set/"),
        ("Reauthenticate", "/accounts/reauthenticate/"),
        ("Social Login Error", "/accounts/social/login/error/"),
        ("Social Login Cancelled", "/accounts/social/login/cancelled/"),
        ("Social Connections", "/accounts/social/connections/"),
    ]

    preview_items = "".join(
        f'<li><a href="{url}">{label}</a> <span class="desc">— {desc}</span></li>'
        for label, url, desc in previews
    )
    account_items = "".join(
        f'<li><a href="{url}">{label}</a></li>'
        for label, url in account_pages
    )

    html = _PREVIEW_HTML.format(preview_items=preview_items, account_items=account_items)
    return HttpResponse(html, content_type="text/html; charset=utf-8")


@require_GET
def error_preview_status(request: HttpRequest, status_code: int) -> HttpResponse:
    if not settings.DEBUG:
        raise Http404()
    if status_code not in _TITLES:
        return _html(404)
    return _html(status_code)
