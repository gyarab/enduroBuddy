# Auth UI Redesign & Email Templates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sjednotit design auth stránek s EB design systémem (dark Google button, role selector karty, přepracovaný brand pane) a vytvořit EB-branded světlé HTML emaily.

**Architecture:** Veškerý auth flow běží jako Vue SPA na `/accounts/*` URL (Django servuje `spa.html`, Vue Router obsluhuje routes). Logic je v `AuthFlowView.vue`, shell v `AuthPreviewShell.vue`. E-maily jsou Django allauth HTML templaty v `backend/templates/account/email/`. Žádné nové soubory — jen úpravy stávajících.

**Tech Stack:** Vue 3 + TypeScript (scoped CSS, `<script setup>`), Django templates (table-based HTML email)

---

## Přehled souborů

| Soubor | Akce | Co se mění |
|--------|------|-----------|
| `frontend/src/views/auth/AuthFlowView.vue` | Modify | Dark Google button; role selector karty; `shellConfig` stats |
| `frontend/src/components/auth/AuthPreviewShell.vue` | Modify | Props interface; brand pane grid bg; 2 stat řádky s ikonami |
| `backend/templates/account/email/base_message.html` | Modify | EB-branded base (bílý card, lime CTA slot, Inter font stack) |
| `backend/templates/account/email/email_confirmation_message.html` | Modify | Lime CTA tlačítko |
| `backend/templates/account/email/password_reset_key_message.html` | Modify | Lime CTA tlačítko |

---

## Task 1: Dark Google button v `AuthFlowView.vue`

**Files:**
- Modify: `frontend/src/views/auth/AuthFlowView.vue` — CSS sekce, třída `.auth-flow-button--google`

Aktuální styl používá světlý gradient (`#fbfbfc → #e8e9ed`). Nahradit za dark surface.

- [ ] **Step 1: Najít a nahradit CSS blok `.auth-flow-button--google`**

V `frontend/src/views/auth/AuthFlowView.vue` najdi blok:
```css
.auth-flow-button--google {
  justify-content: flex-start;
  border-color: rgba(255, 255, 255, 0.08);
  background: linear-gradient(180deg, #fbfbfc 0%, #e8e9ed 100%);
  color: #18181b;
}
```

Nahraď za:
```css
.auth-flow-button--google {
  justify-content: flex-start;
  border-color: var(--eb-border);
  background: var(--eb-surface);
  color: var(--eb-text);
}

.auth-flow-button--google:hover {
  border-color: rgba(255, 255, 255, 0.18);
  background: var(--eb-surface-hover);
}
```

- [ ] **Step 2: Ověřit — spustit dev server**

```bash
cd frontend && npm run dev
```

Otevři `/accounts/login/` v prohlížeči. Google button musí mít tmavé pozadí (`#18181b`), světlý text a hover efekt.

- [ ] **Step 3: Spustit testy — musí být zelené**

```bash
cd frontend && npm test
```

Expected: všechny testy PASS (žádná logika se nemění).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/auth/AuthFlowView.vue
git commit -m "style(auth): dark Google login button"
```

---

## Task 2: Role selector — vizuální karty v signup formuláři

**Files:**
- Modify: `frontend/src/views/auth/AuthFlowView.vue` — template (signup sekce) + CSS

Aktuálně role = `<select>` dropdown. Nahradit dvěma kliknutelnými kartami (Sportovec / Trenér) s barevným indikátorem (lime / blue).

- [ ] **Step 1: Nahradit `<select>` pro roli v signup sekci**

Najdi v template sekci `screen === 'signup'` tento blok:
```html
<label class="auth-flow-field">
  <span>Role</span>
  <select v-model="signupForm.role">
    <option value="ATHLETE">Svěřenec</option>
    <option value="COACH">Trenér</option>
  </select>
  <small v-if="firstError('role')" class="is-danger">{{ firstError("role") }}</small>
</label>
```

Nahraď za:
```html
<div class="auth-flow-field">
  <span>Jsem</span>
  <div class="auth-role-grid">
    <button
      type="button"
      class="auth-role-card"
      :class="{ 'auth-role-card--active-lime': signupForm.role === 'ATHLETE' }"
      @click="signupForm.role = 'ATHLETE'"
    >
      <span class="auth-role-card__dot auth-role-card__dot--lime"></span>
      <span class="auth-role-card__name">Sportovec</span>
      <span class="auth-role-card__desc">Plánuji a zapisuji tréninky</span>
    </button>
    <button
      type="button"
      class="auth-role-card"
      :class="{ 'auth-role-card--active-blue': signupForm.role === 'COACH' }"
      @click="signupForm.role = 'COACH'"
    >
      <span class="auth-role-card__dot auth-role-card__dot--blue"></span>
      <span class="auth-role-card__name">Trenér</span>
      <span class="auth-role-card__desc">Vedu atlety a připravuji plány</span>
    </button>
  </div>
  <small v-if="firstError('role')" class="is-danger">{{ firstError("role") }}</small>
</div>
```

- [ ] **Step 2: Přidat CSS pro role karty**

Do `<style scoped>` sekce `AuthFlowView.vue` přidej na konec:
```css
.auth-role-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.625rem;
}

.auth-role-card {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 0.875rem;
  border-radius: 0.75rem;
  border: 1px solid var(--eb-border);
  background: var(--eb-bg);
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s, background 0.15s;
}

.auth-role-card:hover {
  border-color: rgba(255, 255, 255, 0.14);
}

.auth-role-card--active-lime {
  border-color: rgba(200, 255, 0, 0.28);
  background: linear-gradient(180deg, rgba(200, 255, 0, 0.07) 0%, transparent 100%);
}

.auth-role-card--active-blue {
  border-color: rgba(56, 189, 248, 0.28);
  background: linear-gradient(180deg, rgba(56, 189, 248, 0.07) 0%, transparent 100%);
}

.auth-role-card__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.auth-role-card__dot--lime { background: var(--eb-lime); }
.auth-role-card__dot--blue { background: var(--eb-blue); }

.auth-role-card__name {
  font-size: 0.8125rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--eb-text);
}

.auth-role-card__desc {
  font-size: 0.6875rem;
  color: var(--eb-text-muted);
  line-height: 1.4;
}
```

- [ ] **Step 3: Ověřit vizuálně**

Otevři `/accounts/signup/`. Sekce Role musí zobrazovat 2 karty vedle sebe. Kliknutím na kartu se zvýrazní příslušnou barvou (lime = Sportovec, blue = Trenér). Výchozí stav: Sportovec je vybrán.

- [ ] **Step 4: Spustit testy**

```bash
cd frontend && npm test
```

Expected: všechny testy PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/auth/AuthFlowView.vue
git commit -m "style(auth): replace role select with visual card selector"
```

---

## Task 3: Redesign brand pane v `AuthPreviewShell.vue`

**Files:**
- Modify: `frontend/src/components/auth/AuthPreviewShell.vue` — props, template, CSS

Aktuální brand pane má jednu velkou lime stat kartu s textem. Cíl: 2 kompaktní řádky s ikonou, label a hodnotou. Přidat mřížkový overlay na pozadí jako v preview.

- [ ] **Step 1: Aktualizovat props a template**

Přepis celého souboru `frontend/src/components/auth/AuthPreviewShell.vue`:

```vue
<script setup lang="ts">
defineProps<{
  brandEyebrow: string;
  brandTitle: string;
  brandDescription: string;
  stats?: Array<{ icon: string; label: string; value: string; blue?: boolean }>;
}>();
</script>

<template>
  <section class="auth-shell">
    <aside class="auth-shell__brand">
      <div class="auth-shell__grid-overlay" aria-hidden="true"></div>

      <div class="auth-shell__logo">
        <span class="auth-shell__mark" aria-hidden="true">
          <span></span>
          <span></span>
          <span></span>
        </span>
        <span>EnduroBuddy</span>
      </div>

      <div class="auth-shell__copy">
        <div class="auth-shell__eyebrow">{{ brandEyebrow }}</div>
        <h2>{{ brandTitle }}</h2>
        <p>{{ brandDescription }}</p>
      </div>

      <div v-if="stats?.length" class="auth-shell__stats">
        <div
          v-for="stat in stats"
          :key="stat.label"
          class="auth-shell__stat"
        >
          <div class="auth-shell__stat-icon" :class="{ 'auth-shell__stat-icon--blue': stat.blue }">
            {{ stat.icon }}
          </div>
          <div>
            <div class="auth-shell__stat-label">{{ stat.label }}</div>
            <div class="auth-shell__stat-value">{{ stat.value }}</div>
          </div>
        </div>
      </div>

      <slot name="brand-extra" />
    </aside>

    <div class="auth-shell__content">
      <div class="auth-shell__card">
        <slot />
      </div>
    </div>
  </section>
</template>

<style scoped>
.auth-shell {
  display: grid;
  grid-template-columns: minmax(19rem, 1.02fr) minmax(0, 1fr);
  min-height: 41rem;
  overflow: hidden;
  border: 1px solid var(--eb-border);
  border-radius: 1.5rem;
  background: linear-gradient(180deg, rgba(24, 24, 27, 0.98) 0%, rgba(14, 14, 16, 0.98) 100%);
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.42);
}

.auth-shell__brand {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.75rem;
  border-right: 1px solid var(--eb-border);
  background:
    radial-gradient(ellipse at 80% 15%, rgba(200, 255, 0, 0.10) 0%, transparent 55%),
    radial-gradient(ellipse at 10% 88%, rgba(56, 189, 248, 0.07) 0%, transparent 50%),
    var(--eb-bg);
  overflow: hidden;
}

.auth-shell__grid-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: radial-gradient(ellipse at 40% 40%, rgba(0, 0, 0, 0.55) 30%, transparent 75%);
  pointer-events: none;
}

.auth-shell__logo {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-h3-size);
  font-weight: 700;
  letter-spacing: var(--eb-type-h3-tracking);
}

.auth-shell__mark {
  display: inline-flex;
  align-items: flex-end;
  gap: 0.2rem;
  height: 1.15rem;
  transform: skewX(-6deg);
}

.auth-shell__mark span {
  width: 0.3125rem;
  border-radius: 0.15rem;
  background: var(--eb-lime);
  box-shadow: 0 0 10px rgba(200, 255, 0, 0.20);
}

.auth-shell__mark span:nth-child(1) { height: 0.44rem; opacity: 0.35; }
.auth-shell__mark span:nth-child(2) { height: 0.75rem; opacity: 0.65; }
.auth-shell__mark span:nth-child(3) { height: 1.15rem; }

.auth-shell__copy {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 0.875rem;
  margin-top: auto;
  max-width: 30ch;
}

.auth-shell__eyebrow {
  color: var(--eb-text-muted);
  font-size: var(--eb-type-label-size);
  font-weight: 700;
  letter-spacing: calc(var(--eb-type-label-tracking) + 0.03em);
  text-transform: uppercase;
}

.auth-shell__copy h2 {
  margin: 0;
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-h1-size);
  font-weight: var(--eb-type-h1-weight);
  line-height: var(--eb-type-h1-line);
  letter-spacing: var(--eb-type-h1-tracking);
}

.auth-shell__copy p {
  margin: 0;
  color: var(--eb-text-soft);
  font-size: var(--eb-type-body-size);
  line-height: var(--eb-type-body-line);
}

.auth-shell__stats {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 0.625rem;
}

.auth-shell__stat {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 0.875rem;
  border: 1px solid var(--eb-border);
  border-radius: 0.75rem;
  background: rgba(9, 9, 11, 0.5);
}

.auth-shell__stat-icon {
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  background: rgba(200, 255, 0, 0.10);
  border: 1px solid rgba(200, 255, 0, 0.18);
  display: grid;
  place-items: center;
  font-size: 0.9375rem;
  flex-shrink: 0;
}

.auth-shell__stat-icon--blue {
  background: rgba(56, 189, 248, 0.10);
  border-color: rgba(56, 189, 248, 0.18);
}

.auth-shell__stat-label {
  font-size: 0.6875rem;
  color: var(--eb-text-muted);
  line-height: 1.3;
}

.auth-shell__stat-value {
  font-family: var(--eb-font-mono);
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--eb-text);
  letter-spacing: -0.01em;
}

.auth-shell__content {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.75rem;
}

.auth-shell__card {
  width: min(100%, 29rem);
  padding: 1.75rem;
  border: 1px solid var(--eb-border);
  border-radius: 1.25rem;
  background: linear-gradient(180deg, rgba(24, 24, 27, 0.98) 0%, rgba(16, 16, 18, 0.98) 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

@media (max-width: 960px) {
  .auth-shell {
    grid-template-columns: 1fr;
  }

  .auth-shell__brand {
    min-height: 14rem;
    border-right: 0;
    border-bottom: 1px solid var(--eb-border);
  }

  .auth-shell__copy h2 {
    font-size: var(--eb-type-h2-size);
  }
}
</style>
```

- [ ] **Step 2: Ověřit — dev server**

Otevři `/accounts/login/` nebo `/accounts/signup/`. Levá strana musí zobrazovat mřížku v pozadí, logo, nadpis a (pokud jsou stats) 2 kompaktní řádky se stats.

- [ ] **Step 3: Spustit testy**

```bash
cd frontend && npm test
```

Expected: PASS (žádná logika se nemění, jen props interface).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/auth/AuthPreviewShell.vue
git commit -m "style(auth): redesign brand pane — grid bg, 2 stat rows with icons"
```

---

## Task 4: Aktualizovat `shellConfig` v `AuthFlowView.vue`

**Files:**
- Modify: `frontend/src/views/auth/AuthFlowView.vue` — `shellConfig` computed + template binding

`AuthPreviewShell` má nové props: `stats` místo `statLabel/Value/Description`. Je potřeba:
1. Aktualizovat `shellConfig` computed — nahradit `statLabel/Value/Description` za `stats: [...]`
2. Aktualizovat binding v template — `v-bind="shellConfig"` by měl fungovat automaticky

- [ ] **Step 1: Aktualizovat `shellConfig` computed**

Najdi v `AuthFlowView.vue` funkci `shellConfig` (computed). Má formát:
```ts
return {
  eyebrow: "...",
  title: "...",
  description: "...",
  statLabel: "...",
  statValue: "...",
  statDescription: "...",
}
```

Přejmenuj klíče: `eyebrow → brandEyebrow`, `title → brandTitle`, `description → brandDescription`, a nahraď `statLabel/Value/Description` za `stats`. Každý case vrátí 2 stat objekty.

Příklad pro `login`:
```ts
case "login":
default:
  return {
    brandEyebrow: "Training Workspace",
    brandTitle: "Vrať se do plánu.",
    brandDescription: "Všechny plány, aktivity a spolupráce na jednom místě.",
    stats: [
      { icon: "📅", label: "Aktivní plán", value: "Duben 2026 · 4. týden" },
      { icon: "⚡", label: "Poslední trénink", value: "Dlouhý výběh · 28.4 km", blue: true },
    ],
  };
```

Příklad pro `signup`:
```ts
case "signup":
  return {
    brandEyebrow: "Start Clean",
    brandTitle: "Začni plánovat chytře.",
    brandDescription: "Registrace za minutu. Plán od prvního dne.",
    stats: [
      { icon: "🏃", label: "Pro sportovce", value: "Plán · Trénink · Analýza" },
      { icon: "🎯", label: "Pro trenéry", value: "Skupiny · Plány · Přehled", blue: true },
    ],
  };
```

Příklad pro `password-reset` a `password-reset-done`:
```ts
case "password-reset":
case "password-reset-done":
  return {
    brandEyebrow: "Recovery",
    brandTitle: "Vrátíme tě zpět.",
    brandDescription: "Obnova hesla bez tření. Link přijde na tvůj e-mail.",
    stats: [
      { icon: "🔒", label: "Bezpečný reset", value: "E-mail odkaz" },
      { icon: "✓", label: "Po obnově", value: "Přímý vstup do app", blue: true },
    ],
  };
```

Pro ostatní screeny (`password-reset-key`, `password-reset-key-done`, `verification-sent`, `email-confirm-key`, `logout`, `inactive`, `social-error`, `social-cancelled`, `email-management`, `password-change`, `password-set`, `reauthenticate`, `connections`):
```ts
// Použij stejnou strukturu — 2 stats dle kontextu screenu
// security screeny:
stats: [
  { icon: "🔐", label: "Zabezpečení", value: "Session Auth" },
  { icon: "✓",  label: "Po akci", value: "Návrat do app", blue: true },
],
```

- [ ] **Step 2: Zkontrolovat binding v template**

Najdi v template `AuthFlowView.vue` místo kde je `AuthPreviewShell` použit. Bude vypadat přibližně:
```html
<AuthPreviewShell
  :brandEyebrow="shellConfig.eyebrow"
  :brandTitle="shellConfig.title"
  ...
>
```

Nebo může používat `v-bind`. Aktualizuj binding aby odpovídal novým prop názvům z `shellConfig`. Pokud je použit `v-bind="shellConfig"`, stačí pouze aktualizovat `shellConfig` computed (klíče musí odpovídat prop názvům).

- [ ] **Step 3: Ověřit TypeScript kompilaci**

```bash
cd frontend && npx tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 4: Ověřit vizuálně**

Otevři `/accounts/login/` a `/accounts/signup/`. Levý panel musí zobrazovat správný nadpis, popis a 2 stat řádky pro každou obrazovku.

- [ ] **Step 5: Spustit testy**

```bash
cd frontend && npm test
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/auth/AuthFlowView.vue
git commit -m "feat(auth): update shellConfig to use new stats[] prop interface"
```

---

## Task 5: Email base template — EB branded

**Files:**
- Modify: `backend/templates/account/email/base_message.html`

Cíl: bílé pozadí, EB logo jako text, lime akcent v header proužku, Inter font stack, subtilní border/shadow, footer.

- [ ] **Step 1: Přepsat `base_message.html`**

```html
{% load i18n %}
{% get_current_language as CURRENT_LANGUAGE %}
<!doctype html>
<html lang="{% if CURRENT_LANGUAGE == 'en' %}en{% else %}cs{% endif %}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>EnduroBuddy</title>
</head>
<body style="margin:0;padding:0;background:#f4f4f5;font-family:'Inter',ui-sans-serif,'Segoe UI',Arial,sans-serif;-webkit-font-smoothing:antialiased;">

<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4f4f5;padding:32px 0 48px;">
  <tr>
    <td align="center" style="padding:0 16px;">

      <!-- Card -->
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:600px;background:#ffffff;border:1px solid #e4e4e7;border-radius:14px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.07);">

        <!-- Header -->
        <tr>
          <td style="padding:0;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
              <tr>
                <td style="padding:3px 0 0;background:#c8ff00;font-size:0;line-height:0;">&nbsp;</td>
              </tr>
              <tr>
                <td style="padding:20px 28px 18px;border-bottom:1px solid #f0f0f1;">
                  <span style="font-family:'Inter',ui-sans-serif,'Segoe UI',Arial,sans-serif;font-size:18px;font-weight:700;color:#09090b;letter-spacing:-.03em;">EnduroBuddy</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:28px 28px 24px;font-family:'Inter',ui-sans-serif,'Segoe UI',Arial,sans-serif;font-size:15px;line-height:1.65;color:#18181b;">
            {% block content %}{% endblock content %}
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:18px 28px 22px;border-top:1px solid #f0f0f1;font-family:'Inter',ui-sans-serif,'Segoe UI',Arial,sans-serif;font-size:12px;line-height:1.5;color:#71717a;">
            {% if CURRENT_LANGUAGE == 'en' %}
              You're receiving this email because of your account at {{ current_site.domain }}.
            {% else %}
              Tento e-mail obdržíš v souvislosti se svým účtem na {{ current_site.domain }}.
            {% endif %}
          </td>
        </tr>

      </table>
      <!-- /Card -->

    </td>
  </tr>
</table>

</body>
</html>
```

- [ ] **Step 2: Ověřit — otevřít šablonu v prohlížeči**

Vytvoř lokální HTML soubor nebo použij Django management command pro preview e-mailu. Musí zobrazovat bílou kartu se zlatým proužkem nahoře, EB logem a správnou strukturou.

Alternativně: zkontroluj syntaxi přes Django shell:
```bash
cd backend
python manage.py shell -c "
from django.template.loader import render_to_string
html = render_to_string('account/email/base_message.html', {'current_site': type('S', (), {'domain': 'endurobuddy.local', 'name': 'EnduroBuddy'})()})
print(html[:500])
"
```

Expected: výstup začíná `<!doctype html>` bez chyb.

- [ ] **Step 3: Commit**

```bash
git add backend/templates/account/email/base_message.html
git commit -m "style(email): EB-branded base email template — white card, lime accent"
```

---

## Task 6: Email confirmation template — lime CTA

**Files:**
- Modify: `backend/templates/account/email/email_confirmation_message.html`

Nahradit tmavé tlačítko (`#212529`) lime tlačítkem (`#c8ff00` s tmavým textem). Zlepšit strukturu odstavců.

- [ ] **Step 1: Přepsat `email_confirmation_message.html`**

```html
{% extends "account/email/base_message.html" %}
{% load account %}
{% load i18n %}
{% get_current_language as CURRENT_LANGUAGE %}

{% block content %}
{% user_display user as user_display %}

<p style="margin:0 0 16px 0;color:#52525b;font-size:14px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;">
  {% if CURRENT_LANGUAGE == 'en' %}Email Verification{% else %}Ověření e-mailu{% endif %}
</p>

<p style="margin:0 0 14px 0;">
  {% if CURRENT_LANGUAGE == 'en' %}
    Hi {{ user_display }},
  {% else %}
    Ahoj {{ user_display }},
  {% endif %}
</p>

<p style="margin:0 0 22px 0;">
  {% if CURRENT_LANGUAGE == 'en' %}
    An account was created on EnduroBuddy. Please confirm your email address to activate it.
  {% else %}
    Na EnduroBuddy byl vytvořen účet. Potvrď svou e-mailovou adresu kliknutím na tlačítko níže.
  {% endif %}
</p>

{% if code %}

<p style="margin:0 0 10px 0;font-size:14px;color:#52525b;">
  {% if CURRENT_LANGUAGE == 'en' %}Verification code:{% else %}Ověřovací kód:{% endif %}
</p>

<p style="margin:0 0 22px 0;font-size:28px;font-weight:700;letter-spacing:.12em;color:#09090b;font-family:'JetBrains Mono',ui-monospace,'Cascadia Code',monospace;">{{ code }}</p>

{% else %}

<table role="presentation" cellspacing="0" cellpadding="0" style="margin:0 0 20px 0;">
  <tr>
    <td style="border-radius:8px;background:#c8ff00;">
      <a href="{{ activate_url }}" style="display:inline-block;padding:13px 22px;font-family:'Inter',ui-sans-serif,'Segoe UI',Arial,sans-serif;font-size:14px;font-weight:700;color:#09090b;text-decoration:none;border-radius:8px;letter-spacing:.01em;">
        {% if CURRENT_LANGUAGE == 'en' %}Confirm email address{% else %}Potvrdit e-mailovou adresu{% endif %}
      </a>
    </td>
  </tr>
</table>

<p style="margin:0 0 18px 0;font-size:12px;color:#71717a;">
  {% if CURRENT_LANGUAGE == 'en' %}
    If the button doesn't work, open this link:
  {% else %}
    Pokud tlačítko nefunguje, otevři tento odkaz:
  {% endif %}<br>
  <a href="{{ activate_url }}" style="color:#2563eb;word-break:break-all;">{{ activate_url }}</a>
</p>

{% endif %}

<p style="margin:0;font-size:13px;color:#71717a;">
  {% if CURRENT_LANGUAGE == 'en' %}
    If you didn't create this account, you can safely ignore this email.
  {% else %}
    Pokud jsi registraci neprováděl(a), tento e-mail ignoruj.
  {% endif %}
</p>

{% endblock content %}
```

- [ ] **Step 2: Ověřit — Django shell**

```bash
cd backend
python manage.py shell -c "
from django.template.loader import render_to_string
html = render_to_string('account/email/email_confirmation_message.html', {
  'user': type('U', (), {'display': 'Jan Novák', '__str__': lambda s: 'jan.novak'})(),
  'activate_url': 'https://endurobuddy.local/accounts/confirm-email/abc123/',
  'current_site': type('S', (), {'domain': 'endurobuddy.local', 'name': 'EnduroBuddy'})(),
})
print('OK — no template errors' if 'Potvrdit' in html else 'ERROR')
"
```

Expected: `OK — no template errors`

- [ ] **Step 3: Commit**

```bash
git add backend/templates/account/email/email_confirmation_message.html
git commit -m "style(email): lime CTA button in email confirmation template"
```

---

## Task 7: Password reset email template — lime CTA

**Files:**
- Modify: `backend/templates/account/email/password_reset_key_message.html`

Nahradit tmavé tlačítko lime tlačítkem, zlepšit strukturu.

- [ ] **Step 1: Přepsat `password_reset_key_message.html`**

```html
{% extends "account/email/base_message.html" %}
{% load i18n %}
{% get_current_language as CURRENT_LANGUAGE %}

{% block content %}

<p style="margin:0 0 16px 0;color:#52525b;font-size:14px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;">
  {% if CURRENT_LANGUAGE == 'en' %}Password Reset{% else %}Obnova hesla{% endif %}
</p>

<p style="margin:0 0 14px 0;">
  {% if CURRENT_LANGUAGE == 'en' %}Hi,{% else %}Ahoj,{% endif %}
</p>

<p style="margin:0 0 22px 0;">
  {% if CURRENT_LANGUAGE == 'en' %}
    We received a request to reset the password for your EnduroBuddy account.
    If you made this request, click the button below to set a new password.
  {% else %}
    Přišla žádost o reset hesla k tvému účtu v EnduroBuddy.
    Pokud jsi o reset požádal(a), klikni na tlačítko a nastav nové heslo.
  {% endif %}
</p>

<table role="presentation" cellspacing="0" cellpadding="0" style="margin:0 0 20px 0;">
  <tr>
    <td style="border-radius:8px;background:#c8ff00;">
      <a href="{{ password_reset_url }}" style="display:inline-block;padding:13px 22px;font-family:'Inter',ui-sans-serif,'Segoe UI',Arial,sans-serif;font-size:14px;font-weight:700;color:#09090b;text-decoration:none;border-radius:8px;letter-spacing:.01em;">
        {% if CURRENT_LANGUAGE == 'en' %}Set new password{% else %}Nastavit nové heslo{% endif %}
      </a>
    </td>
  </tr>
</table>

<p style="margin:0 0 18px 0;font-size:12px;color:#71717a;">
  {% if CURRENT_LANGUAGE == 'en' %}
    If the button doesn't work, open this link:
  {% else %}
    Pokud tlačítko nefunguje, otevři tento odkaz:
  {% endif %}<br>
  <a href="{{ password_reset_url }}" style="color:#2563eb;word-break:break-all;">{{ password_reset_url }}</a>
</p>

{% if username %}
<p style="margin:0 0 14px 0;font-size:13px;color:#71717a;">
  {% if CURRENT_LANGUAGE == 'en' %}
    Your username is: <strong style="color:#18181b;">{{ username }}</strong>
  {% else %}
    Tvoje uživatelské jméno je: <strong style="color:#18181b;">{{ username }}</strong>
  {% endif %}
</p>
{% endif %}

<p style="margin:0;font-size:13px;color:#71717a;">
  {% if CURRENT_LANGUAGE == 'en' %}
    If you didn't request a password reset, you can safely ignore this email.
  {% else %}
    Pokud jsi o reset nežádal(a), tento e-mail můžeš bezpečně ignorovat.
  {% endif %}
</p>

{% endblock content %}
```

- [ ] **Step 2: Ověřit — Django shell**

```bash
cd backend
python manage.py shell -c "
from django.template.loader import render_to_string
html = render_to_string('account/email/password_reset_key_message.html', {
  'password_reset_url': 'https://endurobuddy.local/accounts/password/reset/key/abc-123/',
  'username': 'jan.novak',
  'current_site': type('S', (), {'domain': 'endurobuddy.local', 'name': 'EnduroBuddy'})(),
})
print('OK' if 'c8ff00' in html else 'ERROR — lime color missing')
"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/templates/account/email/password_reset_key_message.html
git commit -m "style(email): lime CTA button in password reset email template"
```

---

## Finální ověření

Po dokončení všech tasků:

- [ ] Spustit celou testovací sadu

```bash
cd frontend && npm test
```

Expected: všechny testy PASS, žádné nové failures.

- [ ] Build bez chyb

```bash
cd frontend && npm run build
```

Expected: build proběhne bez TypeScript nebo Vite chyb.

- [ ] Vizuální průchod v prohlížeči

1. `/accounts/login/` — tmavý Google button ✓
2. `/accounts/signup/` — role selector karty ✓, brand pane se 2 stats ✓
3. `/accounts/password/reset/` — brand pane se 2 stats ✓
4. Všechny ostatní screens zůstávají funkční

---

## Co tento plán NEŘEŠÍ (záměrně)

- Odstranění Django auth templates (`backend/templates/account/*.html`) — to je samostatný krok, až Vue flow je ověřený v produkci
- allauth headless mode — aktuální architektura používá vlastní DRF endpoints, headless allauth je samostatná migrace
- Nové auth screen komponenty / refaktoring `AuthFlowView.vue` — samostatný plán pro budoucí verzi
