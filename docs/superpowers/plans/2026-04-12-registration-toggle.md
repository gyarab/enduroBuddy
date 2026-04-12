# Registration Toggle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `REGISTRATION_ENABLED` env flag that closes new user registration (email + Google OAuth) while keeping login fully functional.

**Architecture:** Allauth adapters (`is_open_for_signup`) are the primary gate. A view-level guard redirects GET to `/accounts/signup/` immediately. A context-processor key exposes the flag to Django templates so landing page buttons can be visually disabled.

**Tech Stack:** Django 5.2, django-allauth, pytest/Django TestCase, Django template engine.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `backend/config/settings.py` | Modify | Add `REGISTRATION_ENABLED` flag + adapter registrations |
| `backend/accounts/adapters.py` | Create | `AccountAdapter` + `SocialAccountAdapter` overriding `is_open_for_signup` |
| `backend/accounts/views.py` | Modify | Guard on GET `/accounts/signup/` when registration disabled |
| `backend/accounts/context_processors.py` | Modify | Expose `registration_enabled` to all templates |
| `backend/templates/public/home.html` | Modify | Conditionally disable 3 CTA buttons |
| `backend/static/css/public-base.css` | Modify | Add `.eb-btn-disabled` utility class |
| `backend/accounts/tests.py` | Modify | Tests for adapters, view guard, context processor, template |

---

### Task 1: Settings flag + allauth adapters

**Files:**
- Create: `backend/accounts/adapters.py`
- Modify: `backend/config/settings.py`
- Modify: `backend/accounts/tests.py`

- [ ] **Step 1: Write the failing tests**

Add at the bottom of `backend/accounts/tests.py`:

```python
from django.test import override_settings
from accounts.adapters import AccountAdapter, SocialAccountAdapter


class RegistrationToggleAdapterTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _request(self):
        req = self.factory.get("/accounts/signup/", HTTP_HOST="localhost")
        req.user = AnonymousUser()
        session_middleware = SessionMiddleware(lambda r: None)
        session_middleware.process_request(req)
        req.session.save()
        setattr(req, "_messages", FallbackStorage(req))
        return req

    @override_settings(REGISTRATION_ENABLED=False)
    def test_account_adapter_closed_when_disabled(self):
        adapter = AccountAdapter(self._request())
        self.assertFalse(adapter.is_open_for_signup(self._request()))

    @override_settings(REGISTRATION_ENABLED=True)
    def test_account_adapter_open_when_enabled(self):
        adapter = AccountAdapter(self._request())
        self.assertTrue(adapter.is_open_for_signup(self._request()))

    @override_settings(REGISTRATION_ENABLED=False)
    def test_social_adapter_closed_when_disabled(self):
        adapter = SocialAccountAdapter(self._request())
        self.assertFalse(adapter.is_open_for_signup(self._request(), sociallogin=None))

    @override_settings(REGISTRATION_ENABLED=True)
    def test_social_adapter_open_when_enabled(self):
        adapter = SocialAccountAdapter(self._request())
        self.assertTrue(adapter.is_open_for_signup(self._request(), sociallogin=None))
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python manage.py test accounts.tests.RegistrationToggleAdapterTests -v 2
```

Expected: ImportError or AttributeError — `accounts.adapters` doesn't exist yet.

- [ ] **Step 3: Create `backend/accounts/adapters.py`**

```python
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return getattr(settings, "REGISTRATION_ENABLED", True)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return getattr(settings, "REGISTRATION_ENABLED", True)
```

- [ ] **Step 4: Add setting + register adapters in `backend/config/settings.py`**

Add after the `GARMIN_CONNECT_ENABLED` line (around line 297):

```python
REGISTRATION_ENABLED = os.environ.get("REGISTRATION_ENABLED", "true").lower() == "true"
```

Add after the `ACCOUNT_RATE_LIMITS` block (after line 247):

```python
ACCOUNT_ADAPTER = "accounts.adapters.AccountAdapter"
SOCIALACCOUNT_ADAPTER = "accounts.adapters.SocialAccountAdapter"
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend && python manage.py test accounts.tests.RegistrationToggleAdapterTests -v 2
```

Expected: 4 tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/accounts/adapters.py backend/config/settings.py backend/accounts/tests.py
git commit -m "feat: add REGISTRATION_ENABLED flag and allauth adapters"
```

---

### Task 2: View guard on GET /accounts/signup/

**Files:**
- Modify: `backend/accounts/views.py`
- Modify: `backend/accounts/tests.py`

- [ ] **Step 1: Write the failing test**

Add to `backend/accounts/tests.py` inside `RegistrationToggleAdapterTests`:

```python
    @override_settings(REGISTRATION_ENABLED=False)
    def test_signup_get_redirects_to_login_when_disabled(self):
        response = self.client.get(reverse("account_signup"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("account_login"))

    @override_settings(REGISTRATION_ENABLED=True)
    def test_signup_get_renders_page_when_enabled(self):
        response = self.client.get(reverse("account_signup"))
        self.assertEqual(response.status_code, 200)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python manage.py test accounts.tests.RegistrationToggleAdapterTests.test_signup_get_redirects_to_login_when_disabled accounts.tests.RegistrationToggleAdapterTests.test_signup_get_renders_page_when_enabled -v 2
```

Expected: Both FAIL — signup GET currently returns 200 regardless.

- [ ] **Step 3: Add guard to `backend/accounts/views.py`**

Find the `spa_account_signup` function (line 36) and update it:

```python
def spa_account_signup(request, *args, **kwargs):
    if request.method == "GET" and not settings.REGISTRATION_ENABLED:
        return redirect(reverse("account_login"))
    if request.method == "GET":
        return _spa_or_public(request, path="accounts/signup")
    return account_views.signup(request, *args, **kwargs)
```

Also add `settings` import at the top of `backend/accounts/views.py` — it's not there yet. Add it after the existing Django imports (line 11):

```python
from django.conf import settings
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python manage.py test accounts.tests.RegistrationToggleAdapterTests -v 2
```

Expected: All 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/accounts/views.py backend/accounts/tests.py
git commit -m "feat: redirect signup GET to login when REGISTRATION_ENABLED=false"
```

---

### Task 3: Context processor — expose flag to templates

**Files:**
- Modify: `backend/accounts/context_processors.py`
- Modify: `backend/accounts/tests.py`

- [ ] **Step 1: Write the failing test**

Add to `backend/accounts/tests.py` inside `RegistrationToggleAdapterTests`:

```python
    @override_settings(REGISTRATION_ENABLED=False)
    def test_context_processor_exposes_false_when_disabled(self):
        response = self.client.get(reverse("public_home"))
        self.assertFalse(response.context["registration_enabled"])

    @override_settings(REGISTRATION_ENABLED=True)
    def test_context_processor_exposes_true_when_enabled(self):
        response = self.client.get(reverse("public_home"))
        self.assertTrue(response.context["registration_enabled"])
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python manage.py test accounts.tests.RegistrationToggleAdapterTests.test_context_processor_exposes_false_when_disabled accounts.tests.RegistrationToggleAdapterTests.test_context_processor_exposes_true_when_enabled -v 2
```

Expected: KeyError — `registration_enabled` not in context yet.

- [ ] **Step 3: Add key to `backend/accounts/context_processors.py`**

In the `return` dict at the end of `role_flags()` (line 33), add one entry:

```python
    return {
        "is_coach": is_coach,
        "profile_pending_coach_requests": pending_coach_requests,
        "profile_approved_coach_links": approved_coach_links,
        "app_notifications": app_notifications,
        "dashboard_asset_version": str(getattr(settings, "DASHBOARD_ASSET_VERSION", "50")),
        "registration_enabled": getattr(settings, "REGISTRATION_ENABLED", True),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python manage.py test accounts.tests.RegistrationToggleAdapterTests -v 2
```

Expected: All 8 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/accounts/context_processors.py backend/accounts/tests.py
git commit -m "feat: expose registration_enabled to template context"
```

---

### Task 4: Landing page — disabled CTA buttons + CSS

**Files:**
- Modify: `backend/templates/public/home.html`
- Modify: `backend/static/css/public-base.css`
- Modify: `backend/accounts/tests.py`

- [ ] **Step 1: Write the failing test**

Add to `backend/accounts/tests.py` inside `RegistrationToggleAdapterTests`:

```python
    @override_settings(REGISTRATION_ENABLED=False)
    def test_home_page_signup_buttons_disabled_when_registration_off(self):
        response = self.client.get(reverse("public_home"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        # No link to signup URL
        self.assertNotIn('href="/accounts/signup/"', content)
        # Disabled class present
        self.assertIn("eb-btn-disabled", content)

    @override_settings(REGISTRATION_ENABLED=True)
    def test_home_page_signup_buttons_active_when_registration_on(self):
        response = self.client.get(reverse("public_home"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('href="/accounts/signup/"', content)
        self.assertNotIn("eb-btn-disabled", content)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python manage.py test accounts.tests.RegistrationToggleAdapterTests.test_home_page_signup_buttons_disabled_when_registration_off accounts.tests.RegistrationToggleAdapterTests.test_home_page_signup_buttons_active_when_registration_on -v 2
```

Expected: FAIL — template still always links to signup.

- [ ] **Step 3: Update `backend/templates/public/home.html` — topbar button (line 17)**

Replace:
```html
  <a class="eb-btn-nav lp-btn-cta" href="{% url 'account_signup' %}">{% if CURRENT_LANGUAGE == "en" %}Start free{% else %}Začít zdarma{% endif %}</a>
```

With:
```html
  {% if registration_enabled %}
  <a class="eb-btn-nav lp-btn-cta" href="{% url 'account_signup' %}">{% if CURRENT_LANGUAGE == "en" %}Start free{% else %}Začít zdarma{% endif %}</a>
  {% else %}
  <a class="eb-btn-nav lp-btn-cta eb-btn-disabled">{% if CURRENT_LANGUAGE == "en" %}Start free{% else %}Začít zdarma{% endif %}</a>
  {% endif %}
```

- [ ] **Step 4: Update hero CTA button (line 35)**

Replace:
```html
          <a class="lp-btn lp-btn-primary lp-btn-lg lp-btn-pill" href="{% url 'account_signup' %}">{% if CURRENT_LANGUAGE == "en" %}Try for free{% else %}Vyzkoušet zdarma{% endif %}</a>
```

With:
```html
          {% if registration_enabled %}
          <a class="lp-btn lp-btn-primary lp-btn-lg lp-btn-pill" href="{% url 'account_signup' %}">{% if CURRENT_LANGUAGE == "en" %}Try for free{% else %}Vyzkoušet zdarma{% endif %}</a>
          {% else %}
          <a class="lp-btn lp-btn-primary lp-btn-lg lp-btn-pill eb-btn-disabled">{% if CURRENT_LANGUAGE == "en" %}Try for free{% else %}Vyzkoušet zdarma{% endif %}</a>
          {% endif %}
```

- [ ] **Step 5: Update bottom CTA button (line 149)**

Replace:
```html
          <a class="lp-btn lp-btn-primary lp-btn-lg lp-btn-pill" href="{% url 'account_signup' %}">{% if CURRENT_LANGUAGE == "en" %}Start free →{% else %}Začít zdarma →{% endif %}</a>
```

With:
```html
          {% if registration_enabled %}
          <a class="lp-btn lp-btn-primary lp-btn-lg lp-btn-pill" href="{% url 'account_signup' %}">{% if CURRENT_LANGUAGE == "en" %}Start free →{% else %}Začít zdarma →{% endif %}</a>
          {% else %}
          <a class="lp-btn lp-btn-primary lp-btn-lg lp-btn-pill eb-btn-disabled">{% if CURRENT_LANGUAGE == "en" %}Start free →{% else %}Začít zdarma →{% endif %}</a>
          {% endif %}
```

- [ ] **Step 6: Add `.eb-btn-disabled` to `backend/static/css/public-base.css`**

Find the end of the button/utility section (search for existing `.eb-btn` classes, or add at the end of the file). Add:

```css
/* ── Disabled state (registration closed) ─────────────── */
.eb-btn-disabled {
    opacity: 0.38;
    pointer-events: none;
    cursor: default;
}
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
cd backend && python manage.py test accounts.tests.RegistrationToggleAdapterTests -v 2
```

Expected: All 10 tests pass.

- [ ] **Step 8: Run the full accounts test suite to catch regressions**

```bash
cd backend && python manage.py test accounts -v 2
```

Expected: All tests pass.

- [ ] **Step 9: Commit**

```bash
git add backend/templates/public/home.html backend/static/css/public-base.css backend/accounts/tests.py
git commit -m "feat: disable signup CTA buttons on landing page when REGISTRATION_ENABLED=false"
```

---

### Task 5: Final verification

- [ ] **Step 1: Run full test suite**

```bash
cd backend && python manage.py test -v 2
```

Expected: All tests pass.

- [ ] **Step 2: Manual smoke test with registration disabled**

Add `REGISTRATION_ENABLED=false` to `.env`, restart Django (`python manage.py runserver`), then verify:

- `GET /accounts/signup/` → redirects to `/accounts/login/` ✓
- `POST /accounts/signup/` (via curl or browser) → allauth rejects, redirects to login ✓
- `GET /accounts/login/` → login page loads normally ✓
- Landing page `/` → CTA buttons appear grayed out, no link to signup ✓
- Login page → can log in with existing account ✓

- [ ] **Step 3: Restore `.env` to `REGISTRATION_ENABLED=true` (or remove the key)**
