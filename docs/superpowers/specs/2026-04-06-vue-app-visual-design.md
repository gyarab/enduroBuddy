# EnduroBuddy Vue App — Vizuální design spec

**Datum:** 2026-04-06  
**Kontext:** Vizuální design Vue SPA (přihlášená část aplikace) — `/app/*` a `/coach/*`  
**Design language:** Neon Lab × Swiss Precision (viz `docs/visual-style-guide.md`)

---

## Principy pro aplikační část

Veřejná sekce (landing page) je marketing — extravagantní, hero typografie, glow efekty.  
**Aplikační část je workspace** — disciplinovanější, hustší informace, méně hluku. Stejné tokeny, jiné proporce:

- Méně whitespace než landing page — data jsou na prvním místě
- Akcenty (lime, blue) chirurgicky — jen pro stav a CTA, ne dekoraci
- Mono font dominuje tam kde jsou data — pace, km, HR, časy
- Žádné gradienty v datech — čistá plocha, jasná čitelnost

---

## 1. AppShell — celkový layout

```
┌─────────────────────────────────────────────────────────┐
│  TOPNAV  56px  bg: #111113  border-bottom: #27272a       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  MAIN CONTENT  bg: #09090b                               │
│  max-width: 1280px, auto margins, padding: 0 24px        │
│                                                          │
└─────────────────────────────────────────────────────────┘

Coach varianta:
┌─────────────────────────────────────────────────────────┐
│  TOPNAV  56px                                            │
├────────────┬────────────────────────────────────────────┤
│  SIDEBAR   │                                            │
│  280px     │  MAIN CONTENT                              │
│  bg:       │  bg: #09090b                               │
│  #111113   │                                            │
│  border-r  │                                            │
│  #27272a   │                                            │
└────────────┴────────────────────────────────────────────┘
```

**AppShell.vue:**
- `min-height: 100vh`, `background: var(--eb-bg)`
- Sidebar je pevný (`position: sticky, top: 56px, height: calc(100vh - 56px), overflow-y: auto`)
- Na mobilu sidebar se schovává za hamburger v topnav

---

## 2. TopNav

```
┌──────────────────────────────────────────────────────────┐
│  [EB Logo compact]  · · ·             [🔔 3] [Avatar ▼]  │
│  24px left                               24px right pad  │
└──────────────────────────────────────────────────────────┘
```

**Specifikace:**
- Výška: 56px
- Background: `#111113` (`--eb-bg-elevated`)
- Border-bottom: 1px solid `#27272a`
- `backdrop-filter: blur(12px)` — při scrollu obsah "projíždí pod" nav
- `position: sticky, top: 0, z-index: 100`

**Logo (vlevo):**
- `eb-logo-compact.svg` — mark + "EB"
- Výška: 28px
- Margin-left: 24px
- Kliknutí → `/app/`

**Střed (athlete view):**
- Měsíc navigator: `← Duben 2026 →`
- Šipky: ghost ikona-button (24px, hover bg `#27272a`, radius 6px)
- Název měsíce: Syne 700, 15px, `#fafafa`, min-width 140px, text-align center
- Rok: Inter 400, 13px, `#71717a`, display inline za názvem pokud ≠ current year

**Střed (coach view):**
- Stejný měsíc navigator + vlevo od šipek pill badge s jménem aktivního atleta
- Athlete pill: `bg: rgba(56,189,248,.12)`, `border: 1px solid rgba(56,189,248,.20)`, `color: #38bdf8`, Inter 600 11px, radius-full, 28px výška

**Vpravo:**
- Notification bell (`EbNotificationBell.vue`):
  - Ghost button 36×36px, radius-md
  - Bell ikona 18px, `#a1a1aa`
  - Unread badge: 18px circle, `bg: #c8ff00`, `color: #09090b`, Inter 700 10px, `position: absolute, top: 4px, right: 4px`
  - Hover: bg `#27272a`
- Profile avatar (36×36px circle):
  - Initials z jména, `bg: #27272a`, `color: #fafafa`, Inter 600 13px
  - Hover: ring 1px `#c8ff00`
  - Click → dropdown (profil, odhlásit)

**Profile dropdown:**
- `bg: #18181b`, border 1px `#27272a`, radius-md, shadow-lg
- Položky: Inter 500 14px, padding 10px 16px
- Divider: 1px `#27272a`
- Odhlásit: `color: #f43f5e`

---

## 3. Athlete Dashboard — hlavní pohled

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  TOPNAV (s měsíc navigatorem)                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  [MONTH SUMMARY BAR]                         24px top   │
│                                                          │
│  [WEEK 1 CARD]                               16px gap   │
│  [WEEK 2 CARD]                               16px gap   │
│  [WEEK 3 CARD]                               16px gap   │
│  [WEEK 4 CARD]                               16px gap   │
│  [WEEK 5 CARD?]                              24px bot   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Month Summary Bar

Horizontální řada 4 stat karet — celkový přehled měsíce:

```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  TRÉNINKY    │ │  KILOMETRY   │ │  ČAS         │ │  SPLNĚNÍ     │
│  12 / 16     │ │  187.4 km    │ │  14h 32m     │ │  75 %        │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

**Každá karta:**
- `bg: #18181b`, border 1px `#27272a`, radius-md, padding 16px 20px
- Label: Inter 600 11px uppercase tracking 0.06em, `#71717a`
- Hodnota: JetBrains Mono 500 22px, `#fafafa`
- Subtext (X/Y nebo %): Inter 400 12px, `#71717a`
- Splnění karta: hodnota `#c8ff00` pokud ≥ 80%, `#f59e0b` pokud 50–79%, `#f43f5e` pokud < 50%

### Week Card

```
┌─────────────────────────────────────────────────────────┐
│  TÝDEN 14  ·  31. 3 – 6. 4  ·  [45.2 km] [4h 12m]     │  ← header
├─────────────────────────────────────────────────────────┤
│  [TRAINING ROW]                                          │
│  [TRAINING ROW]                                          │
│  [TRAINING ROW]                                          │
│  [+ přidat trénink]  (jen coach)                        │
└─────────────────────────────────────────────────────────┘
```

**Week Card header:**
- `bg: #111113` (tmavší než karta)
- Border-bottom: 1px `#27272a`
- Padding: 12px 20px
- "TÝDEN 14": Inter 600 11px uppercase tracking 0.08em, `#71717a`
- Datum range: Inter 400 13px, `#a1a1aa`, margin-left 12px
- Stats (vpravo): JetBrains Mono 500 13px, `#a1a1aa` — km + čas aktuálního týdne

**Week Card body:**
- `bg: #18181b`
- Border: 1px solid `#27272a`
- Border-radius: radius-md (10px)
- Overflow hidden (header má jiný bg)

---

## 4. Training Row — klíčový element

Každý řádek = jeden plánovaný trénink. Existují tři stavy:

### Stav: Plánováno (jen plán, neuplynulý den)

```
│ ▌  [Tempo běh]          [15 km · 70min]   [Z2]  [Thurs]  │
│    Příjemné tempo, cadence 165+                           │
```

- Levý border 3px: `#38bdf8` (blue — planned)
- Background: `#18181b`
- Padding: 14px 20px 14px 17px (kompenzace left border)

### Stav: Splněno

```
│ ▌  [Tempo běh]          [16.2 km · 68min · 138 bpm]  ✓  │
│    Šlo to dobře dnes                                      │
```

- Levý border 3px: `#c8ff00` (lime — done)
- Background: `#18181b`
- Čísla: JetBrains Mono, `#c8ff00`

### Stav: Nesplněno (uplynulý den bez záznamu)

```
│ ─  [Tempo běh]          [15 km · 70min]             ✗   │
```

- Levý border 3px: rgba(244,63,94,0.5) (faded danger)
- Background: `#18181b`
- Název: `#71717a` (muted)

### Training Row anatomy

```
[LEFT-BORDER 3px] [SESSION-TYPE ICON 16px] [TITLE flex-1] [DATA] [STATUS-BADGE] [DAY-LABEL]
```

**Session type icon** (16px, vlevo od titulku):
- Malá tečka nebo piktogram tréninkové zóny — `#71717a` pro plánované, `#c8ff00` pro splněné

**Title:**
- Inter 500 14px, `#fafafa`
- Pokud má poznámku: druhý řádek Inter 400 12px, `#71717a`, margin-top 2px

**Data (vpravo od titulku):**
- JetBrains Mono 500 13px
- Planned: `#a1a1aa` — "15 km · 1:10:00"
- Completed: `#c8ff00` — "16.2 km · 1:08:23 · 138 bpm"
- Odděleno ` · ` (středník s mezerou)

**Status badge:**
- `EbBadge` komponenta — viz visual-style-guide.md specifikace badges
- Planned: blue pill "PLÁN"
- Done: lime pill "HOTOVO"
- Missed: red pill "VYNECHÁNO"

**Day label (vpravo):**
- Inter 600 11px uppercase, `#71717a`
- "PO" / "ÚT" / "ST" atd.

**Hover state (celý řádek):**
- Background: `#1f1f23` (surface-hover)
- Cursor: pointer
- Transition: background 150ms ease-out

**Second phase trénink:**
- Odsazený řádek s left-padding 32px
- Menší písmo (13px), tlumenější barvy
- Spojovací linie vlevo (1px dashed `#27272a`)

---

## 5. Inline Editor — expanded training row

Po kliknutí na training row se řádek expanduje do editoru (ne modal — inline):

```
┌─────────────────────────────────────────────────────────┐
│ ▌  [Tempo běh]                              [✕ zavřít] │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  [──────────────────── TEXTAREA ────────────────────]   │
│   Příjemné tempo, cadence 165+, 3×1000m @4:15           │
│                                                          │
│  Parsed preview:                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  INTERVAL 1    1000 m    4:15 / km    4:15 tot  │    │
│  │  INTERVAL 2    1000 m    4:15 / km    4:15 tot  │    │
│  │  INTERVAL 3    1000 m    4:15 / km    4:15 tot  │    │
│  └─────────────────────────────────────────────────┘    │
│  Celkem: 15 km · cca 1:10:00                            │
│                                                          │
│  [Uložit]                              [Přidat 2. fázi] │
└─────────────────────────────────────────────────────────┘
```

**Editor container:**
- `bg: #111113`, border 1px `#c8ff00` (lime — aktivní editor), radius-md
- Shadow: `--eb-glow-lime` (0 0 20px rgba(200,255,0,.15))
- Padding: 16px 20px

**Textarea:**
- `bg: #09090b`, border 1px `#27272a`, radius-sm
- Focus: border `#c8ff00`, glow-lime box-shadow
- Font: JetBrains Mono 500 14px (tréninkový zápis je data)
- Min-height: 80px, auto-expand
- `color: #fafafa`, placeholder `#71717a`

**Parsed preview tabulka:**
- Viditelná jen pokud parser detekuje intervaly / strukturu
- `bg: rgba(200,255,0,.04)`, border 1px `rgba(200,255,0,.12)`, radius-sm
- Header: Inter 600 10px uppercase tracking 0.08em, `#71717a`
- Values: JetBrains Mono 500 12px, `#c8ff00`
- Animuje se in při parsingu (fade + translateY(4px))

**Tlačítka:**
- "Uložit": Primary button (lime bg, dark text)
- "Přidat 2. fázi": Secondary button
- "Zavřít" (×): Ghost button vpravo nahoře

---

## 6. Completed Training Editor

Podobný inline editor ale pro zápis splněného tréninku:

```
┌─────────────────────────────────────────────────────────┐
│ ▌  [Tempo běh]  PLÁN: 15 km · 1:10:00      [✕ zavřít] │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  SKUTEČNOST                                              │
│  [  km  ] ·  [  min  ] ·  [HR avg  ] ·  [HR max  ]     │
│                                                          │
│  POZNÁMKA                                                │
│  [──────────── TEXTAREA ────────────────────────────]   │
│                                                          │
│                                    [Uložit jako hotové] │
└─────────────────────────────────────────────────────────┘
```

**Pole (km, min, HR):**
- Inline inputs 80px šířka, vedle sebe s `·` separátorem
- `bg: #09090b`, border `#27272a`, radius-sm, výška 36px
- Font: JetBrains Mono 500 14px
- Focus: border lime, glow
- Placeholder hodnota = plánovaná hodnota (dimmed)

**"Uložit jako hotové" button:**
- Full-width na mobilu, auto-width desktop
- Lime primary button

---

## 7. Coach Sidebar

```
┌────────────────┐
│  ATLETI   [+]  │  ← Inter 600 11px uppercase + invite button
├────────────────┤
│  [●] Jan Novák │  ← aktivní atlet (lime dot + lime text)
│  [○] Eva Malá  │
│  [○] Petr K.   │
│  [○] Marie B.  │
├────────────────┤
│  SKUPINY       │
│  [○] Skupina A │
└────────────────┘
```

**Sidebar:**
- Width: 260px (desktop), collapsible na mobilu
- `bg: #111113`, border-right 1px `#27272a`
- Padding: 16px 0

**Section header:**
- Inter 600 11px uppercase tracking 0.08em, `#71717a`
- Padding: 0 16px, margin-bottom 8px
- "+" button: ghost icon button 20px, `#71717a`, hover `#fafafa`

**Athlete row:**
- Padding: 8px 16px
- Výška: 40px
- Inter 500 14px, `#a1a1aa`
- Dot: 8px circle vlevo, `#27272a`
- Hover: bg `#18181b`, text `#fafafa`
- Aktivní: dot `#c8ff00`, text `#fafafa`, bg `rgba(200,255,0,.06)`, border-left 2px `#c8ff00`

---

## 8. Notification Dropdown

Po kliknutí na bell ikonu:

```
┌──────────────────────────────────┐
│  NOTIFIKACE              [Vše]   │
├──────────────────────────────────┤
│  [●] Jan Novák přidal výsledek   │
│      Tempo běh · před 2 min      │
├──────────────────────────────────┤
│  [○] Eva splnila týden           │
│      před 1 hod                  │
└──────────────────────────────────┘
```

- `bg: #18181b`, border 1px `#27272a`, radius-md, shadow-lg
- Width: 320px
- Max-height: 400px, overflow-y auto
- Animace: fade + translateY(-8px) → 0 (150ms ease-out)

**Notification item:**
- Padding: 12px 16px
- Border-bottom: 1px `#27272a` (ne na posledním)
- Text: Inter 400 13px, `#fafafa`
- Meta (čas): Inter 400 11px, `#71717a`
- Unread dot: 8px `#c8ff00`, position absolute vlevo
- Unread item: bg `rgba(200,255,0,.04)`
- Hover: bg `#1f1f23`

---

## 9. Garmin Import Modal

```
┌─────────────────────────────────────────────────────────┐
│  Import z Garmin                               [✕]      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Synchronizuji aktivity...                              │
│                                                          │
│  ████████████████░░░░░░░░  68 %                         │
│  Načítám aktivity z posledních 30 dní                   │
│                                                          │
│  ✓  Tempo běh  16. 3. 2026  16.2 km                    │
│  ✓  Easy run   15. 3. 2026  10.5 km                    │
│  ⟳  Zpracovávám...                                      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Modal:** `EbModal.vue` — `bg: #18181b`, radius-lg, shadow-xl, overlay blur

**Progress bar:**
- Track: `#27272a`, height 4px, radius-full
- Fill: `#c8ff00`, animace width transition 300ms ease-out
- Procento: JetBrains Mono 500 13px, `#c8ff00`, vpravo od baru

**Activity list:**
- Každý řádek: Inter 400 13px
- ✓ checkmark: `#c8ff00`
- Spinner (⟳): animovaný, `#71717a`
- Údaje: JetBrains Mono pro distance

---

## 10. Responzivita

### Breakpointy

```
Mobile:   < 768px
Tablet:   768px – 1024px
Desktop:  > 1024px
```

### Adaptace

**Mobile:**
- Sidebar schovává (hamburger v topnav)
- Month Summary Bar: 2×2 grid místo 1×4 řady
- Training Row: data na druhém řádku pod titulkem
- Inline editor: full-screen overlay (ne inline expand)
- Topnav: logo + hamburguer + notifikace (měsíc navigator přesune pod nav jako 48px bar)

**Tablet:**
- Sidebar collapsible (výchozí: skrytý pro atleta, viditelný pro coacha)
- Training rows: stejné jako desktop
- Month summary: 4 karty na řadě (menší padding)

**Desktop:**
- Plný layout podle wireframů výše

---

## 11. Přechody a animace

Dle `visual-style-guide.md` motion principů:

| Akce | Duration | Easing | Efekt |
|------|----------|--------|-------|
| Row hover | 150ms | ease-out | background |
| Row expand (editor) | 200ms | ease-out | height + opacity |
| Modal open | 200ms | ease-out | opacity + translateY(-8px)→0 |
| Modal close | 150ms | ease-in | opacity + translateY(-8px) |
| Notification dropdown | 150ms | ease-out | opacity + translateY(-4px)→0 |
| Toast slide-in | 300ms | ease-out | translateX(100%)→0 |
| Toast slide-out | 200ms | ease-in | translateX(100%) |
| Progress bar fill | 300ms | ease-out | width |
| Parsed preview | 200ms | ease-out | opacity + translateY(4px)→0 |

Žádné bounce, elastic, ani dekorativní animace — pohyb jen pro orientaci.

---

## 12. Prázdné stavy

**Prázdný měsíc (žádné tréninky naplánovány):**
```
┌─────────────────────────────────────────────────────────┐
│                                                          │
│              ≡≡ ≡≡≡ ≡≡≡≡≡                               │
│         (velocity bars logo, opacity 0.15)               │
│                                                          │
│           Zatím žádný plán pro tento měsíc              │
│           Požádej svého trenéra o sestavení plánu        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

- Logo mark: `opacity: 0.12`, 48px
- Text: Inter 400 14px, `#71717a`, text-align center
- Padding: 64px 24px

**Coach bez atletů:**
- Stejný styl + button "Pozvat atleta" (primary)

---

## 13. Loading states

**Skeleton pro week cards** (při načítání měsíce):
- Placeholders stejného layoutu jako karty
- `bg: #18181b`, animated shimmer: `background: linear-gradient(90deg, #18181b 25%, #27272a 50%, #18181b 75%)`
- `background-size: 200% 100%`, `animation: shimmer 1.5s infinite`
- Žádné spinner animace pro hlavní obsah — skeleton preferován

**Inline spinner** (loading button):
- Button text nahrazen 16px spinner (`border: 2px solid rgba(9,9,11,.3); border-top: 2px solid #09090b`)
- Button disabled, opacity 0.8

---

## Shrnutí vizuálního jazyka v aplikaci

| Prvek | Vizuální signál |
|-------|----------------|
| Plánovaný trénink | Blue left border + blue badge |
| Splněný trénink | Lime left border + lime badge + lime čísla |
| Nesplněný trénink | Faded red left border + muted text |
| Aktivní editor | Lime outline + lime glow |
| Coach UI akcenty | Lime (stejná role jako "done") |
| Athlete UI akcenty | Blue (stejná role jako "planned") |
| Datové hodnoty | JetBrains Mono vždy |
| Navigace a labely | Inter uppercase, muted |
| Nadpisy sekcí | Syne (jen kde je potřeba personalita) |
