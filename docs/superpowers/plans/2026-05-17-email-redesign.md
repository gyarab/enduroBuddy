# Email Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Přepsat 3 HTML emailové šablony do Auth Card Match designu — lime/blue top-border karta, dark default + light mode overrides přes `@media`, system fonts.

**Architecture:** `base_message.html` definuje kompletní wrapper (outer, karta, header, footer) s `{% block card_border_style %}` pro přepis accent barvy v child šablonách. `email_confirmation_message.html` a `password_reset_key_message.html` rozšiřují base a dodávají pouze obsah bloku `content` + případný přepis `card_border_style`. Žádné Python změny.

**Tech Stack:** Django templates, inline CSS + `@media (prefers-color-scheme: light)` v `<head>`, table-based layout pro kompatibilitu s Outlookem, system font stack.

---

### Task 1: Přepsat `base_message.html`

**Files:**
- Modify: `backend/templates/account/email/base_message.html`

- [ ] **Step 1: Přepsat soubor**

Celý obsah souboru nahradit:

```html
{% load i18n %}
{% get_current_language as CURRENT_LANGUAGE %}
<!doctype html>
<html lang="{% if CURRENT_LANGUAGE == 'en' %}en{% else %}cs{% endif %}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark light">
  <meta name="supported-color-schemes" content="dark light">
  <title>EnduroBuddy</title>
  <style>
    @media (prefers-color-scheme: light) {
      .eb-outer       { background: #f4f4f5 !important; }
      .eb-card        { background: #ffffff !important; border-color: #e4e4e7 !important; box-shadow: 0 4px 24px rgba(0,0,0,0.07) !important; }
      .eb-header      { border-color: #f0f0f2 !important; }
      .eb-bar         { background: #09090b !important; }
      .eb-wordmark    { color: #09090b !important; }
      .eb-eyebrow     { color: #71717a !important; }
      .eb-headline    { color: #09090b !important; }
      .eb-greeting    { color: #52525b !important; }
      .eb-text        { color: #52525b !important; }
      .eb-fallback    { color: #a1a1aa !important; }
      .eb-fallback a  { color: #2563eb !important; }
      .eb-disclaimer  { color: #a1a1aa !important; }
      .eb-footer      { border-color: #f0f0f2 !important; }
      .eb-footer-text { color: #a1a1aa !important; }
      .eb-footer-link { color: #a1a1aa !important; }
    }
  </style>
</head>
<body style="margin:0;padding:0;background:#09090b;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;-webkit-font-smoothing:antialiased;">

<table class="eb-outer" role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#09090b;padding:32px 0 48px;">
  <tr>
    <td align="center" style="padding:0 16px;">

      <table class="eb-card" role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:600px;background:#18181b;border:1px solid #27272a;{% block card_border_style %}border-top:2px solid #c8ff00;{% endblock %}border-radius:14px;overflow:hidden;box-shadow:0 24px 64px rgba(0,0,0,0.4),inset 0 1px 0 rgba(255,255,255,0.03);">

        <!-- Header -->
        <tr>
          <td class="eb-header" style="padding:16px 24px 14px;border-bottom:1px solid #1f1f22;">
            <table role="presentation" cellspacing="0" cellpadding="0">
              <tr valign="bottom">
                <td class="eb-bar" style="width:4px;height:8px;background:#c8ff00;border-radius:2px;padding:0;"></td>
                <td style="width:3px;padding:0;"></td>
                <td class="eb-bar" style="width:4px;height:13px;background:#c8ff00;border-radius:2px;padding:0;"></td>
                <td style="width:3px;padding:0;"></td>
                <td class="eb-bar" style="width:4px;height:18px;background:#c8ff00;border-radius:2px;padding:0;"></td>
                <td style="width:10px;padding:0;"></td>
                <td style="padding:0;vertical-align:middle;">
                  <span class="eb-wordmark" style="font-size:15px;font-weight:700;color:#fafafa;letter-spacing:-0.02em;">EnduroBuddy</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Content -->
        <tr>
          <td style="padding:28px 24px 24px;">
            {% block content %}{% endblock content %}
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td class="eb-footer" style="padding:12px 24px 18px;border-top:1px solid #1f1f22;">
            <p class="eb-footer-text" style="margin:0;font-size:11px;line-height:1.55;color:#3f3f46;">
              {% if CURRENT_LANGUAGE == 'en' %}
                You're receiving this email because of your account at <a class="eb-footer-link" href="https://{{ current_site.domain }}" style="color:#52525b;text-decoration:underline;">{{ current_site.domain }}</a>.
              {% else %}
                Tento e-mail obdržíš v souvislosti se svým účtem na <a class="eb-footer-link" href="https://{{ current_site.domain }}" style="color:#52525b;text-decoration:underline;">{{ current_site.domain }}</a>.
              {% endif %}
            </p>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>

</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add backend/templates/account/email/base_message.html
git commit -m "style: redesign email base template (Auth Card Match)"
```

---

### Task 2: Přepsat `email_confirmation_message.html`

**Files:**
- Modify: `backend/templates/account/email/email_confirmation_message.html`

- [ ] **Step 1: Přepsat soubor**

```html
{% extends "account/email/base_message.html" %}
{% load account %}
{% load i18n %}
{% get_current_language as CURRENT_LANGUAGE %}

{% block content %}
{% user_display user as user_display %}

<p class="eb-eyebrow" style="margin:0 0 10px;font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#71717a;">
  {% if CURRENT_LANGUAGE == 'en' %}Email Verification{% else %}Ověření e-mailu{% endif %}
</p>

<p class="eb-headline" style="margin:0 0 6px;font-size:22px;font-weight:700;line-height:1.15;letter-spacing:-0.03em;color:#fafafa;">
  {% if CURRENT_LANGUAGE == 'en' %}Confirm your email{% else %}Potvrď svůj e-mail{% endif %}
</p>

<p class="eb-greeting" style="margin:0 0 6px;font-size:14px;line-height:1.5;color:#a1a1aa;">
  {% if CURRENT_LANGUAGE == 'en' %}Hi {{ user_display }},{% else %}Ahoj {{ user_display }},{% endif %}
</p>

<p class="eb-text" style="margin:0 0 24px;font-size:14px;line-height:1.65;color:#a1a1aa;">
  {% if CURRENT_LANGUAGE == 'en' %}
    An account was created on EnduroBuddy. Click the button below to confirm your email address and activate it.
  {% else %}
    Na EnduroBuddy byl vytvořen účet. Klikni na tlačítko níže a e-mailová adresa bude ověřena a účet aktivován.
  {% endif %}
</p>

{% if code %}

<p class="eb-text" style="margin:0 0 8px;font-size:13px;color:#71717a;">
  {% if CURRENT_LANGUAGE == 'en' %}Verification code:{% else %}Ověřovací kód:{% endif %}
</p>
<p style="margin:0 0 24px;font-size:28px;font-weight:700;letter-spacing:0.12em;color:#c8ff00;font-family:'Courier New',Courier,monospace;">{{ code }}</p>

{% else %}

<table role="presentation" cellspacing="0" cellpadding="0" style="margin:0 0 16px;">
  <tr>
    <td style="border-radius:8px;background:#c8ff00;">
      <a href="{{ activate_url }}" style="display:inline-block;padding:12px 24px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;font-size:13px;font-weight:700;color:#09090b;text-decoration:none;border-radius:8px;letter-spacing:0.01em;">
        {% if CURRENT_LANGUAGE == 'en' %}Confirm email address{% else %}Potvrdit e-mailovou adresu{% endif %}
      </a>
    </td>
  </tr>
</table>

<p class="eb-fallback" style="margin:0 0 16px;font-size:11px;color:#3f3f46;line-height:1.6;">
  {% if CURRENT_LANGUAGE == 'en' %}If the button doesn't work, open this link:{% else %}Pokud tlačítko nefunguje, otevři tento odkaz:{% endif %}<br>
  <a href="{{ activate_url }}" style="color:#38bdf8;word-break:break-all;text-decoration:none;">{{ activate_url }}</a>
</p>

{% endif %}

<p class="eb-disclaimer" style="margin:0;font-size:12px;line-height:1.6;color:#3f3f46;">
  {% if CURRENT_LANGUAGE == 'en' %}
    If you didn't create this account, you can safely ignore this email.
  {% else %}
    Pokud jsi registraci neprováděl(a), tento e-mail ignoruj.
  {% endif %}
</p>

{% endblock content %}
```

- [ ] **Step 2: Ověřit rendering šablony (Django shell)**

Spustit z kořene projektu (načte `.env` automaticky):

```bash
cd backend && python -c "
import os, django, pathlib
for line in (pathlib.Path('..') / '.env').read_text().splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, _, v = line.partition('='); os.environ.setdefault(k.strip(), v.strip())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory
from allauth.account.models import EmailAddress
from allauth.account.internal.flows import email_verification

User = get_user_model()
TARGET = 'vojta.holcman@outlook.cz'
TEMP = '__test__@endurobuddy.local'
User.objects.filter(username=TEMP).delete()
user = User.objects.create_user(username=TEMP, email=TARGET, first_name='Vojta', last_name='Holcman', password='Tmp123!')
ea = EmailAddress.objects.create(user=user, email=TARGET, primary=True, verified=False)
rf = RequestFactory()
req = rf.get('/')
req.META.update({'SERVER_NAME': 'endurobuddy.cz', 'SERVER_PORT': '443', 'wsgi.url_scheme': 'https'})
req.session = SessionStore(); req._messages = FallbackStorage(req); req.user = user
email_verification.send_verification_email_to_address(req, ea)
User.objects.filter(username=TEMP).delete()
print('Verification email sent to', TARGET)
"
```

Očekávaný výstup: `Verification email sent to vojta.holcman@outlook.cz`

Zkontrolovat email v schránce — ověřit:
- Lime top-border na kartě
- Eyebrow „Ověření e-mailu" / „Email Verification"
- Headline, greeting, CTA tlačítko
- Footer s klikatelným odkazem na endurobuddy.cz
- Light mode (otevřít v Apple Mail nebo přepnout téma v prohlížeči)

- [ ] **Step 3: Commit**

```bash
git add backend/templates/account/email/email_confirmation_message.html
git commit -m "style: redesign email verification template (Auth Card Match)"
```

---

### Task 3: Přepsat `password_reset_key_message.html`

**Files:**
- Modify: `backend/templates/account/email/password_reset_key_message.html`

- [ ] **Step 1: Přepsat soubor**

```html
{% extends "account/email/base_message.html" %}
{% load account %}
{% load i18n %}
{% get_current_language as CURRENT_LANGUAGE %}

{% block card_border_style %}border-top:2px solid #38bdf8;{% endblock %}

{% block content %}
{% user_display user as user_display %}

<p class="eb-eyebrow" style="margin:0 0 10px;font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#38bdf8;">
  {% if CURRENT_LANGUAGE == 'en' %}Password Reset{% else %}Obnova hesla{% endif %}
</p>

<p class="eb-headline" style="margin:0 0 6px;font-size:22px;font-weight:700;line-height:1.15;letter-spacing:-0.03em;color:#fafafa;">
  {% if CURRENT_LANGUAGE == 'en' %}Reset your password{% else %}Obnov své heslo{% endif %}
</p>

<p class="eb-greeting" style="margin:0 0 6px;font-size:14px;line-height:1.5;color:#a1a1aa;">
  {% if CURRENT_LANGUAGE == 'en' %}Hi {{ user_display }},{% else %}Ahoj {{ user_display }},{% endif %}
</p>

<p class="eb-text" style="margin:0 0 24px;font-size:14px;line-height:1.65;color:#a1a1aa;">
  {% if CURRENT_LANGUAGE == 'en' %}
    We received a request to reset the password for your EnduroBuddy account. Click the button below to set a new password.
  {% else %}
    Obdrželi jsme žádost o reset hesla k tvému účtu EnduroBuddy. Klikni na tlačítko níže a nastav si nové heslo.
  {% endif %}
</p>

<table role="presentation" cellspacing="0" cellpadding="0" style="margin:0 0 16px;">
  <tr>
    <td style="border-radius:8px;background:#c8ff00;">
      <a href="{{ password_reset_url }}" style="display:inline-block;padding:12px 24px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;font-size:13px;font-weight:700;color:#09090b;text-decoration:none;border-radius:8px;letter-spacing:0.01em;">
        {% if CURRENT_LANGUAGE == 'en' %}Set new password{% else %}Nastavit nové heslo{% endif %}
      </a>
    </td>
  </tr>
</table>

<p class="eb-fallback" style="margin:0 0 16px;font-size:11px;color:#3f3f46;line-height:1.6;">
  {% if CURRENT_LANGUAGE == 'en' %}If the button doesn't work, open this link:{% else %}Pokud tlačítko nefunguje, otevři tento odkaz:{% endif %}<br>
  <a href="{{ password_reset_url }}" style="color:#38bdf8;word-break:break-all;text-decoration:none;">{{ password_reset_url }}</a>
</p>

{% if username %}
<p class="eb-text" style="margin:0 0 16px;font-size:13px;color:#3f3f46;">
  {% if CURRENT_LANGUAGE == 'en' %}Username: {{ username }}{% else %}Uživatelské jméno: {{ username }}{% endif %}
</p>
{% endif %}

<p class="eb-disclaimer" style="margin:0;font-size:12px;line-height:1.6;color:#3f3f46;">
  {% if CURRENT_LANGUAGE == 'en' %}
    If you didn't request this, you can safely ignore this email.
  {% else %}
    Pokud jsi reset hesla nepožadoval(a), tento e-mail ignoruj.
  {% endif %}
</p>

{% endblock content %}
```

- [ ] **Step 2: Ověřit rendering šablony (Django shell)**

```bash
cd backend && python -c "
import os, django, pathlib
for line in (pathlib.Path('..') / '.env').read_text().splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, _, v = line.partition('='); os.environ.setdefault(k.strip(), v.strip())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from allauth.account.forms import ResetPasswordForm

User = get_user_model()
TARGET = 'vojta.holcman@outlook.cz'
TEMP = '__test__@endurobuddy.local'
User.objects.filter(username=TEMP).delete()
User.objects.create_user(username=TEMP, email=TARGET, first_name='Vojta', last_name='Holcman', password='Tmp123!')
rf = RequestFactory()
req = rf.get('/')
req.META.update({'SERVER_NAME': 'endurobuddy.cz', 'SERVER_PORT': '443', 'wsgi.url_scheme': 'https'})
form = ResetPasswordForm(data={'email': TARGET})
form.is_valid(); form.save(req)
User.objects.filter(username=TEMP).delete()
print('Password reset email sent to', TARGET)
"
```

Očekávaný výstup: `Password reset email sent to vojta.holcman@outlook.cz`

Zkontrolovat email v schránce — ověřit:
- **Blue** top-border na kartě (odlišení od verifikace)
- Eyebrow „Obnova hesla" v modré barvě `#38bdf8`
- Headline, greeting, CTA tlačítko (lime)
- Footer s klikatelným odkazem

- [ ] **Step 3: Commit**

```bash
git add backend/templates/account/email/password_reset_key_message.html
git commit -m "style: redesign password reset email template (blue accent)"
```

---

### Task 4: Aktualizovat CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Přidat záznam do sekce „Aktivní plány a změny"**

Do `CLAUDE.md` přidat na začátek sekce „Aktivní plány a změny":

```markdown
### 2026-05-17 — Email redesign: Auth Card Match ✅ KOMPLETNÍ

**Spec:** `docs/superpowers/specs/2026-05-17-email-redesign-design.md`
**Plán:** `docs/superpowers/plans/2026-05-17-email-redesign.md`

- `base_message.html`: nový wrapper, lime logo bars (tmavé v light mode), footer s homepage odkazem, `{% block card_border_style %}` pro accent barvu, `@media (prefers-color-scheme: light)` pro dark/light přepínání
- `email_confirmation_message.html`: eyebrow + headline + greeting + CTA + fallback link + disclaimer, lime top-border
- `password_reset_key_message.html`: stejná struktura, blue `#38bdf8` top-border a eyebrow barva
- Fonty: system font stack (`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial`)
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md — email redesign complete"
```
