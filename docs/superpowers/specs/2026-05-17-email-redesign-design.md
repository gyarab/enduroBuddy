# Email Redesign — Spec

**Datum:** 2026-05-17  
**Status:** Schváleno uživatelem

---

## Přehled

Přepracovat HTML emailové šablony (ověření e-mailu, obnova hesla) tak, aby vizuálně odpovídaly designovému systému aplikace „Neon Lab × Swiss Precision" — konkrétně jazyku auth karty z `AuthFlowView.vue`. Fungovat musí v dark i light režimu emailových klientů.

---

## Šablony k úpravě

| Soubor | Obsah |
|--------|-------|
| `backend/templates/account/email/base_message.html` | Základní wrapper, header, footer |
| `backend/templates/account/email/email_confirmation_message.html` | Tělo verifikačního emailu |
| `backend/templates/account/email/email_confirmation_signup_message.html` | Include na `email_confirmation_message.html` — beze změny |
| `backend/templates/account/email/password_reset_key_message.html` | Tělo emailu pro reset hesla |
| `backend/templates/account/email/email_confirmation_subject.txt` | Předmět — beze změny |
| `backend/templates/account/email/password_reset_key_subject.txt` | Předmět — beze změny |
| `backend/templates/account/email/base_message.txt` | Plaintext fallback — beze změny |

---

## Vizuální design (schválený přístup B)

### Outer wrapper
- Dark: `background: #09090b`, padding: `32px 16px 48px`
- Light: `background: #f4f4f5` (přes `@media (prefers-color-scheme: light)`)

### Karta
- `max-width: 600px`, `margin: 0 auto`
- Dark: `background: linear-gradient(180deg, #18181b 0%, #101012 100%)`
- Light: `background: #ffffff`
- `border: 1px solid #27272a` (light: `#e4e4e7`)
- `border-top: 2px solid <accent>` — **lime `#c8ff00`** pro verifikaci, **blue `#38bdf8`** pro reset hesla
- `border-radius: 14px`
- `box-shadow: 0 24px 64px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.03)` (dark); `0 4px 24px rgba(0,0,0,0.07)` (light)

### Header (uvnitř karty)
- Padding: `16px 24px 14px`
- `border-bottom: 1px solid #1f1f22` (light: `#f0f0f2`)
- Logo: 3 HTML bary (Stride Mark) — dark: lime `#c8ff00`, light: tmavé `#09090b` (lime na bílé není vidět)
- Wordmark „EnduroBuddy": dark `#fafafa`, light `#09090b`

### Tělo emailu
- Padding: `28px 24px 24px`
- **Eyebrow**: `11px`, `font-weight: 700`, `letter-spacing: 0.08em`, uppercase — dark i light: `#71717a`; pro reset: `#38bdf8`
- **Headline**: `22px`, `font-weight: 700`, `letter-spacing: -0.03em`, `line-height: 1.15` — dark: `#fafafa`, light: `#09090b`
- **Greeting** „Ahoj [jméno],": `14px` — dark: `#a1a1aa`, light: `#52525b`
- **Body text**: `14px`, `line-height: 1.65` — dark: `#a1a1aa`, light: `#52525b`
- **CTA tlačítko**: `background: #c8ff00`, `color: #09090b`, `font-size: 13px`, `font-weight: 700`, `padding: 12px 24px`, `border-radius: 8px`
- **Fallback link**: `11px`, pod tlačítkem, celá URL — dark: `#38bdf8`, light: `#2563eb`
- **Disclaimer** (ignoruj pokud jsi neregistroval): `12px` — dark: `#3f3f46`, light: `#a1a1aa`

### Footer
- `border-top: 1px solid #1f1f22` (light: `#f0f0f2`)
- Padding: `12px 24px 18px`
- Text: `11px` — dark: `#3f3f46`, light: `#a1a1aa`
- Doména `{{ current_site.domain }}` je klikatelný odkaz na homepage — dark: `color: #52525b`, light: `color: #a1a1aa`

### Fonty
- Stack: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif`
- Žádné external Google Fonts — 100% kompatibilita se všemi klienty (Outlook, Gmail mobilní app, Apple Mail)

---

## Dark / Light mode implementace

Emailoví klienti co **podporují** `@media (prefers-color-scheme: light)`: Apple Mail, Outlook 2019+ (macOS), Gmail web (experimentálně).  
Klienti co **nepodporují**: Gmail Android/iOS app — zobrazí vždy dark verzi (výchozí), což je v pořádku.

Implementace: každý dark-specifický inline styl je override-ován přes `@media (prefers-color-scheme: light)` pravidla v `<style>` tagu v `<head>`. Aby overrides fungovaly přes email klienty, používáme kombinaci:
1. CSS třídy s dark hodnotami jako default
2. `@media (prefers-color-scheme: light)` přepíše barvy tříd

---

## Obsah emailů

### Email 1 — Ověření e-mailu
- Eyebrow: `Email Verification` / `Ověření e-mailu`
- Headline: `Confirm your email` / `Potvrď svůj e-mail`  
- Greeting: `Hi {{ user_display }},` / `Ahoj {{ user_display }},`
- Text: stávající bilingvní obsah — beze změny
- Tlačítko: `Confirm email address` / `Potvrdit e-mailovou adresu` → `{{ activate_url }}`
- Lime top-border

### Email 2 — Obnova hesla
- Eyebrow: `Password Reset` / `Obnova hesla`
- Headline: `Reset your password` / `Obnov své heslo`
- Greeting: `Hi {{ user_display }},` / `Ahoj {{ user_display }},`
- Text: stávající bilingvní obsah — beze změny
- Tlačítko: `Set new password` / `Nastavit nové heslo` → `{{ password_reset_url }}`
- Blue top-border (`#38bdf8`)

---

## Scope

- Pouze `base_message.html`, `email_confirmation_message.html`, `password_reset_key_message.html`
- Plaintext šablony (`.txt`) a předměty (subject) se nemění
- `email_confirmation_signup_message.html` zůstane jako `{% include %}` — beze změny
