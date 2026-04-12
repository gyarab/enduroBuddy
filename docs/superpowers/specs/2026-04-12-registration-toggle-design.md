# Registration Toggle — Design Spec

**Date:** 2026-04-12  
**Status:** Approved

## Overview

Add an environment-variable flag `REGISTRATION_ENABLED` that disables new user registration in demo/closed deployments. When disabled:
- Email/password signup is blocked (GET redirects to login, POST is rejected by allauth)
- Google OAuth is blocked for new accounts (existing users can still log in via Google)
- Login works normally for all existing users
- Landing page CTA buttons ("Začít zdarma" / "Try for free" / "Vyzkoušet zdarma") appear disabled (grayed out, no href)
- Login button on landing page is unaffected

## Environment Variable

```
REGISTRATION_ENABLED=false   # disables all new account creation
REGISTRATION_ENABLED=true    # default — normal behaviour
```

Default is `true` so existing deployments are unaffected without explicit opt-in.

## Changes

### 1. `backend/config/settings.py`

Add one line near the other feature flags (e.g. near `GARMIN_CONNECT_ENABLED`):

```python
REGISTRATION_ENABLED = os.environ.get("REGISTRATION_ENABLED", "true").lower() == "true"
```

### 2. `backend/accounts/adapters.py` (new file)

Allauth provides `is_open_for_signup()` on both account and social-account adapters. Overriding these is the idiomatic way to close registration.

```python
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return settings.REGISTRATION_ENABLED


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return settings.REGISTRATION_ENABLED
```

When `is_open_for_signup()` returns `False`, allauth rejects the signup and redirects to login with an error message — no custom error page needed.

### 3. `backend/config/settings.py` — register adapters

```python
ACCOUNT_ADAPTER = "accounts.adapters.AccountAdapter"
SOCIALACCOUNT_ADAPTER = "accounts.adapters.SocialAccountAdapter"
```

### 4. `backend/accounts/views.py` — view-level guard on GET

`spa_account_signup` currently renders the Vue signup page on GET unconditionally. When registration is disabled, the GET should redirect to login immediately so the user never sees the signup form:

```python
def spa_account_signup(request, *args, **kwargs):
    if request.method == "GET" and not settings.REGISTRATION_ENABLED:
        return redirect(reverse("account_login"))
    ...existing code...
```

POST is left unchanged — the allauth adapter handles it.

### 5. `backend/accounts/context_processors.py` — expose flag to templates

Add `registration_enabled` to the dict returned by `role_flags()`:

```python
return {
    ...existing keys...
    "registration_enabled": getattr(settings, "REGISTRATION_ENABLED", True),
}
```

### 6. `backend/templates/public/home.html` — disabled CTA buttons

Three buttons reference `{% url 'account_signup' %}`. When `registration_enabled` is False, they render as a non-interactive `<span>` (or `<a>` without `href`) with a disabled CSS class.

Pattern for each button:

```html
{% if registration_enabled %}
  <a class="lp-btn lp-btn-primary lp-btn-lg lp-btn-pill" href="{% url 'account_signup' %}">...</a>
{% else %}
  <a class="lp-btn lp-btn-primary lp-btn-lg lp-btn-pill eb-btn-disabled">...</a>
{% endif %}
```

Same pattern for the topbar `eb-btn-nav lp-btn-cta` button.

### 7. `backend/static/css/public-base.css` — disabled button style

Add a utility class (`.eb-btn-disabled`) that makes any button look inactive:

```css
.eb-btn-disabled {
    opacity: 0.38;
    pointer-events: none;
    cursor: default;
}
```

## What is NOT changed

- Login (`/accounts/login/`) — unchanged, always available
- Password reset flow — unchanged
- Django admin — unchanged (superusers can still create accounts via admin)
- Existing Google OAuth users — can still log in normally; only new-account creation is blocked
- API endpoints — unchanged (allauth adapter blocks signup at the allauth level which covers the API path too)

## Testing

- With `REGISTRATION_ENABLED=false`:
  - GET `/accounts/signup/` → 302 to `/accounts/login/`
  - POST `/accounts/signup/` → allauth rejects, redirects to login with error
  - Google OAuth callback for new user → allauth rejects, redirects to login with error
  - GET `/accounts/login/` → works normally
  - Landing page: CTA buttons appear grayed out, login button works
- With `REGISTRATION_ENABLED=true` (or unset):
  - All existing behaviour unchanged
