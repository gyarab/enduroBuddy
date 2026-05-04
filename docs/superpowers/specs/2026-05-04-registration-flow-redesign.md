# Registration Flow Redesign

**Datum:** 2026-05-04  
**Větev:** feat/nuxt-migration (→ main)  
**Status:** Spec schválena, čeká na implementační plán

---

## Přehled

Kompletní přepis registration flow: env toggle pro vypnutí registrace, přidání souhlasu s podmínkami do email i Google signup, nový Google onboarding screen v auth shellu a redesign emailových šablon do dark theme designu aplikace.

---

## Rozsah

### Co je v tomto specu

1. Env toggle `REGISTRATION_ENABLED` — ochrana backendu a frontendu
2. Signup formulář — přidání terms+privacy checkboxu
3. Google first-time flow — nová `/accounts/profile-setup/` stránka v auth shellu
4. Email šablony — redesign do dark theme s light mode fallbackem

### Co není v tomto specu

- Změny v auth flow pro existující uživatele
- Vynucení zpětného souhlasu s terms u existujících účtů
- Změny v admin rozhraní

---

## 1. Env Toggle (již implementováno)

`REGISTRATION_ENABLED=false` v `.env` → backend vrátí `403` na `POST /api/v1/auth/signup/` (implementováno v předchozím commitu).

Frontend čte `/api/v1/site-config/` → `{ registration_enabled: bool }`.

**Landing page:** CTA tlačítka (hero + dolní CTA sekce) jsou `disabled` atributem, vizuálně zašedlá — ne skrytá. Existující uživatelé vidí, že app existuje, ale registrace je uzavřena.

**`/accounts/signup/`:** Vue watch na `screen === 'signup'` + `!registrationEnabled` → `router.replace('/accounts/login/')`. Implementováno.

Tato část nevyžaduje další změny.

---

## 2. Signup Formulář — Terms Checkbox

### Frontend (`AuthFlowView.vue`)

Přidat nový prvek těsně před submit tlačítko v sekci `screen === 'signup'`:

```html
<label class="auth-flow-check auth-flow-check--terms">
  <input v-model="signupForm.termsAccepted" type="checkbox" />
  <span>
    Souhlasím s
    <a href="/terms" target="_blank" rel="noopener">Podmínkami použití</a>
    a
    <a href="/privacy" target="_blank" rel="noopener">Ochranou osobních údajů</a>
  </span>
</label>
<small v-if="firstError('terms_accepted')" class="is-danger">
  {{ firstError('terms_accepted') }}
</small>
```

Submit button dostane `:disabled="isSubmitting || !signupForm.termsAccepted"` — bez zaškrtnutí nelze odeslat.

Přidat `termsAccepted: false` do `signupForm` reactive objektu.

Přidat `terms_accepted` do payloadu `signupWithPassword()` API volání.

### Backend

**`auth_signup` view** — přidat validaci:
```python
if not payload.get("terms_accepted"):
    return JsonResponse(
        {"ok": False, "errors": {"terms_accepted": ["Souhlas s podmínkami je povinný."]}},
        status=400,
    )
```

**`Profile` model** — nové pole:
```python
terms_accepted_at = models.DateTimeField(null=True, blank=True)
```

Po úspěšné registraci: `user.profile.terms_accepted_at = timezone.now()` a `save()`.

Nová migrace: `accounts/migrations/0018_profile_terms_accepted_at.py`.

---

## 3. Google First-Time Flow

### Detekce — `needs_profile_setup`

Přidáme `@property` na `Profile` model (bez nové DB migrace):

```python
@property
def needs_profile_setup(self) -> bool:
    return (
        self.user.socialaccount_set.filter(provider="google").exists()
        and not self.google_role_confirmed
    )
```

Tato property bezpečně odlišuje Google uživatele od email uživatelů — email uživatelé mají `google_role_confirmed = False` také, ale žádný social account, takže `needs_profile_setup` vrátí `False`. Žádná nová DB migrace.

### Redirect po Google auth

`_default_route_for_user()` v `backend/api/views/auth.py` dostane novou větev:

```python
profile = getattr(user, "profile", None)
if profile and profile.needs_profile_setup:
    return _app_url("/accounts/profile-setup/", request)
```

Tato větev nastane pouze pro Google uživatele kteří ještě neprošli onboardingem.

### Nová Nuxt stránka

**`frontend/pages/accounts/profile-setup.vue`**

- Layout: `auth` (stejný jako login/signup — `AuthPreviewShell`)
- Guard: pokud `authStore.user` je null nebo `google_role_confirmed === true`, redirect na `/app/dashboard`
- Formulář:
  - **Jméno** — `<input>` pre-filled z `authStore.user.first_name` (Google ho dodá)
  - **Příjmení** — pre-filled z `authStore.user.last_name`
  - **Role picker** — stejný `auth-role-grid` komponent jako v signup
  - **Terms checkbox** — stejný styl jako v signup
- Submit: `POST /api/v1/auth/profile-setup/`
- Po úspěchu: redirect na `/app/dashboard` nebo `/coach/plans` dle role

`screenMap` v `[...slug].vue` se nepoužívá pro tuto stránku — jde o samostatnou Nuxt page.

### Nový API endpoint

**`POST /api/v1/auth/profile-setup/`**

Přijme: `{ first_name, last_name, role, terms_accepted: true }`

Vyžaduje: přihlášeného uživatele (session cookie), jinak 401.

Uloží do `Profile`:
- `user.first_name`, `user.last_name` (update)
- `profile.role = role`
- `profile.terms_accepted_at = timezone.now()`
- `profile.google_role_confirmed = True`

Vrátí: `{ ok: true, redirect_to: "/app/dashboard" }` nebo `/coach/plans`.

### Middleware guard

**`/api/v1/auth/me` response** dostane nové pole `needs_profile_setup: bool` (computed z `profile.needs_profile_setup` property). Frontend neřeší logiku sám — jen čte tento flag.

`authStore.user` typ se rozšíří o `needs_profile_setup: boolean`.

**`frontend/middleware/profile-setup.global.ts`** — nový globální middleware:

```ts
export default defineNuxtRouteMiddleware((to) => {
  const authStore = useAuthStore()
  if (
    authStore.user?.needs_profile_setup &&
    !to.path.startsWith("/accounts/profile-setup")
  ) {
    return navigateTo("/accounts/profile-setup/")
  }
})
```

Zabraňuje obejití stránky přímou navigací na `/app/dashboard` — dokud Google uživatel nevyplní profil, každá navigace ho vrátí na setup.

---

## 4. Email Šablony — Dark Theme

### Strategie

Primární (default): plně tmavý email — `#09090b` background, `#fafafa` text.  
Fallback pro světlý mód: `@media (prefers-color-scheme: light)` přepne pozadí na světlé, text na tmavý.  
CTA tlačítko (`#c8ff00` na `#09090b` textu) funguje bez změny v obou módech.

Podpora: Apple Mail, iOS Mail, Outlook (macOS), Samsung Mail, Proton Mail. Gmail webový klient (světlý mód) bude vypadat světle — to je správné chování.

### Struktura `base_message.html`

```html
<!DOCTYPE html>
<html lang="cs">
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <meta name="supported-color-schemes" content="light dark">
  <style>
    /* Base dark */
    body, .eb-body { background: #09090b !important; }
    .eb-card { background: #111113; border: 1px solid #27272a; }
    .eb-text { color: #fafafa; }
    .eb-text-muted { color: #71717a; }
    .eb-text-soft { color: #a1a1aa; }

    /* Light mode override */
    @media (prefers-color-scheme: light) {
      body, .eb-body { background: #f4f4f5 !important; }
      .eb-card { background: #ffffff !important; border-color: #e4e4e7 !important; }
      .eb-text { color: #09090b !important; }
      .eb-text-muted { color: #71717a !important; }
      .eb-text-soft { color: #52525b !important; }
      .eb-footer { background: #e4e4e7 !important; }
      .eb-footer-text { color: #71717a !important; }
    }
  </style>
</head>
<body class="eb-body">
  <!-- Header: tmavý vždy, lime bottom border -->
  <table class="eb-header" ...>
    <!-- Stride Mark SVG inline + "EnduroBuddy" text -->
  </table>

  <!-- Card s obsahem -->
  <table class="eb-card" ...>
    <tr><td class="eb-eyebrow eb-text-muted">...</td></tr>
    <tr><td class="eb-title eb-text">...</td></tr>
    <tr><td class="eb-body-text eb-text-soft">...</td></tr>
    <!-- CTA button -->
    <tr><td>
      <a class="eb-cta" style="background:#c8ff00;color:#09090b;...">{% block cta_text %}{% endblock %}</a>
    </td></tr>
    {% block extra_content %}{% endblock %}
  </table>

  <!-- Footer: tmavý, copyright -->
  <table class="eb-footer" ...>
    <tr><td class="eb-footer-text">© {% now "Y" %} EnduroBuddy</td></tr>
  </table>
</body>
</html>
```

Header zůstane tmavý (`#09090b`) vždy — i v light mode. Pouze karta a pozadí body se přepnou.

### Šablony k přepisu

| Šablona | Obsah |
|---------|-------|
| `base_message.html` | Nový tmavý wrapper s media query |
| `base_message.txt` | Beze změny (plain text, bez stylů) |
| `email_confirmation_message.html` | Eyebrow "Email Verification", titulek, text, CTA "Potvrdit e-mail" |
| `email_confirmation_signup_message.html` | Extends confirmation (beze změny logiky) |
| `password_reset_key_message.html` | Eyebrow "Password Reset", CTA "Nastavit nové heslo" |

Logo: Stride Mark SVG inline (z `backend/static/brand/eb-mark.svg`) — nevyžaduje HTTP request, funguje ve všech klientech.

---

## Datový model — souhrn změn

| Model | Pole | Typ | Poznámka |
|-------|------|-----|---------|
| `Profile` | `terms_accepted_at` | `DateTimeField(null=True)` | Timestamp souhlasu s ToS |

Existující pole `google_role_confirmed` (Boolean, default False) se využívá jako příznak completion Google onboardingu — žádná změna.

---

## API — souhrn změn

| Endpoint | Změna |
|----------|-------|
| `POST /api/v1/auth/signup/` | Přijme + validuje `terms_accepted`, uloží `terms_accepted_at` |
| `GET /api/v1/auth/me` | Response přidá pole `needs_profile_setup: bool` (computed) |
| `POST /api/v1/auth/profile-setup/` | **Nový** — Google onboarding: role, terms, jméno |

---

## Testovací strategie

**Backend:**
- `test_signup_terms_required` — 400 bez `terms_accepted`
- `test_signup_saves_terms_accepted_at` — timestamp se uloží
- `test_profile_setup_saves_role_and_terms` — nový endpoint
- `test_profile_setup_requires_auth` — 401 bez session
- `test_profile_setup_marks_google_role_confirmed` — flag se nastaví na True

**Frontend (Vitest):**
- `signup-terms.test.ts` — checkbox disabled → button disabled; checkbox required field error
- `profile-setup.test.ts` — pre-fill z authStore, submit flow

**Emaily:**
- Manuální test v Litmus nebo Mail.app (tmavý + světlý mód)
- `python manage.py send_test_email` — jednoduchý management command pro rychlé ověření
