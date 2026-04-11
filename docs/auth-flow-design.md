# EnduroBuddy Auth Flow Design

## Cíl

Převést autentizační flow do stejného jazyka jako zbytek značky: `Neon Lab × Swiss Precision`. Auth nemá působit jako odtržený bootstrap formulář, ale jako klidný vstup do training workspace.

## Design Direction

- Jeden konzistentní auth shell pro všechny stránky.
- Tmavý základ `#09090b` a elevated surface `#18181b`.
- Lime jako hlavní rozhodovací akce, blue jako podpůrný informační akcent.
- Space Grotesk pro headline, Inter pro UI text, JetBrains Mono jen pro technické štítky a meta.
- Minimum vizuálního šumu: 1 primární CTA na obrazovku, jemné glow pouze na focus a hlavní akci.

## Auth Shell

### Layout

- Desktop: dvousloupcový layout.
- Levý panel je brand/story panel s logem, krátkou hodnotou produktu a mikro metrikou.
- Pravý panel je samotná auth karta.
- Mobile: brand panel se skládá nad formulář a redukuje se na compact hero.

### Background

- Base background je true dark.
- Přes pozadí běží dvě jemné radiální vrstvy:
  - lime haze vpravo nahoře
  - blue haze vlevo dole
- Přes celou plochu je velmi jemný grid pattern, aby plocha nepůsobila plochě.

### Card

- Surface `#18181b`
- Border `1px solid #27272a`
- Radius `24px`
- Shadow `0 24px 64px rgba(0,0,0,.6)`
- Vnitřní padding 32px desktop, 24px mobile

## Shared Components

### Top Meta

- Malý eyebrow label nahoře: `AUTHENTICATION`, `GOOGLE FLOW`, `PASSWORD RESET`, `EMAIL VERIFICATION`
- Inter 11px, uppercase, tracking 0.08em, muted text

### Titles

- H1/H2 ve Space Grotesk 700
- Headline krátká, věcná, bez marketingového tónu
- Pod headline vždy jedno vysvětlující souvětí

### Inputs

- Height 48px
- Background `#09090b`
- Border `#27272a`
- Focus border lime + outer glow
- Label nad fieldem, nikdy jen placeholder
- Error state je text + červený border, ne pouze červený text

### Buttons

- Primary button: lime fill, dark text
- Secondary button: transparent, neutral border
- Social button: světlý surface uvnitř dark shell se silně definovanou ikonou Google a textem zarovnaným na střed
- Tlačítka 48px, radius 10px

### Divider

- Horizontální linka s centrálním labelem `nebo`
- Linka používá `--eb-border-soft`

### Support Text

- Footer text pod formulářem pro přepínání login/signup
- Tonálně klidný, ne příliš světlý

## Screen Inventory

### 1. Login

- Headline: `Vítej zpět`
- Podtext: návrat do tréninkového přehledu a plánů
- Obsah:
  - Google sign-in
  - divider
  - e-mail / username
  - password
  - remember me
  - forgot password link
  - primary CTA `Přihlásit se`
  - přechod na registraci

### 2. Sign Up

- Headline: `Vytvoř si EnduroBuddy účet`
- Form fields:
  - jméno
  - příjmení
  - e-mail
  - role
  - heslo
  - heslo znovu
- Google button je výš než formulář, protože social signup je preferovaný fast path

### 3. Google Continue

- Slouží pro `socialaccount/login.html`
- Krátké potvrzení, že uživatel pokračuje přes Google
- Hlavní CTA `Pokračovat přes Google`
- Sekundární CTA `Zpět`
- Může zobrazit malou info kartičku s textem, co se stane dál

### 4. Google Sign Up Completion

- Slouží pro `socialaccount/signup.html`
- Předvyplněné údaje z Google účtu jsou read-only nebo zvýrazněné jako imported
- Uživatel doplňuje jen to, co chybí
- CTA: `Dokončit registraci`

### 5. Complete Profile

- Slouží pro `account/complete_profile.html`
- Použije se po Google signupu nebo při nedokončeném profilu
- Tři hlavní fieldy:
  - jméno
  - příjmení
  - role
- Vpravo nebo dole malý explainer role rozdílů `Coach` vs `Athlete`

### 6. Password Reset Request

- Headline: `Obnovit heslo`
- Jediný field: e-mail
- Support copy vysvětluje, že přijde odkaz

### 7. Password Reset Sent

- Stavová stránka, ne formulář
- Ikona nebo status chip `EMAIL SENT`
- CTA:
  - `Otevřít e-mail`
  - `Zpět na přihlášení`

### 8. Password Reset New Password

- Fieldy:
  - nové heslo
  - potvrzení hesla
- Bez zbytečných rozptylujících prvků

### 9. Password Reset Done

- Potvrzovací stránka po úspěšné změně hesla
- CTA `Pokračovat na přihlášení`

### 10. Verification Sent

- Informace, že ověřovací e-mail byl odeslán
- Doplňková akce `Poslat znovu`

### 11. Email Confirm

- Stránka pro potvrzení e-mailu
- Stav success / pending podle situace
- CTA:
  - `Potvrdit e-mail`
  - nebo po úspěchu `Pokračovat do aplikace`

### 12. Verified Email Required

- Upozornění, že některá akce vyžaduje ověřený e-mail
- CTA vede na resend verification

### 13. Authentication Error

- Error state pro nepovedený social login
- Červený status chip, jasná lidská věta, žádný technický žargon
- CTA `Zkusit znovu` + `Použít e-mail`

### 14. Login Cancelled

- Neutral state po zrušení Google flow uživatelem
- CTA `Zpět na přihlášení`

### 15. Social Connections

- Přehled propojených účtů
- Každý provider je v řádku jako card row
- Primary action `Připojit Google`, secondary destructive action `Odpojit`

### 16. Logout / Reauthenticate / Ratelimit / Inactive

- Všechny tyto utility obrazovky používají stejnou status-page variantu shellu
- Mění se jen:
  - status chip
  - headline
  - podtext
  - sada CTA

## Content Rules

- Headline max 2 řádky.
- Podtext max 2 krátké věty.
- Primární CTA vždy začíná slovesem.
- Chybové texty formulářů jsou konkrétní, ne generické.
- Google flow explicitně říká, že používá Google účet, ne jen `sociální účet`.

## Accessibility

- Kontrast minimálně WCAG AA.
- Focus ring viditelný i na social buttonu i text linkách.
- Každý status má textový label, ne jen barvu.
- Checkbox a inline links musí mít hit area minimálně 40px.

## Motion

- 120ms hover/focus
- 180ms field validation a button hover
- 300ms entrance auth card
- Žádné bounce animace

## Doporučení pro implementaci

- Vytvořit jeden sdílený auth stylesheet a společný auth shell partial.
- Auth stránky nestavět na bootstrap card komponentách.
- Google button a status pages držet jako reusable varianty, ne jako jednorázový markup.
- Validace a Django messages stylovat v auth shellu stejně jako toast/notifikační systém.

## Deliverables

- Spec: `docs/auth-flow-design.md`
- Preview: `docs/auth-flow-preview.html`
