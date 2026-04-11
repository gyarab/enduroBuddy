# Font System Redesign — Space Grotesk

**Date:** 2026-04-11  
**Status:** Approved  
**Scope:** Typography only — no color, layout, or component changes

---

## Problém

Současná kombinace Syne + Inter + JetBrains Mono funguje, ale Syne má příliš výrazný "art-school" / retro geometrický charakter, který neodpovídá vizi "precision instrument". V hustém UI (dashboard, tabulky) Syne v menších velikostech nefunguje dobře, a proto se de facto nepoužívá pod H2 — hierarchie je nekoherentní.

---

## Rozhodnutí

**Nahradit Syne za Space Grotesk** a optimalizovat typografickou škálu pro nový font.

| Role | Před | Po |
|------|------|----|
| Display / Headlines | Syne 700–800 | Space Grotesk 600–700 |
| Body / UI | Inter 400–600 | Inter 400–600 (beze změny) |
| Numerická data | JetBrains Mono 500 | JetBrains Mono 500 (beze změny) |

Space Grotesk byl zvolen pro svůj technický, precision-nástroj charakter — srovnatelný s nástoji jako Linear, Raycast nebo Vercel. Zachovává diferenci mezi display a body fontem, ale bez retro podtónu Syne.

---

## Nová typografická škála

```
Level     Rodina           Váha   Velikost                  Line-height   Letter-spacing
────────────────────────────────────────────────────────────────────────────────────────
Display   Space Grotesk    700    clamp(2.5rem, 6vw, 4.5rem)  0.95        −0.05em
H1        Space Grotesk    700    clamp(1.75rem, 4vw, 2.75rem) 1.05       −0.04em
H2        Space Grotesk    600    clamp(1.25rem, 2.5vw, 1.75rem) 1.15     −0.025em
H3        Space Grotesk    500    1.0625rem (17px)            1.3         −0.01em
Body      Inter            400    0.9375rem (15px)            1.6          0
Small     Inter            500    0.8125rem (13px)            1.5         +0.01em
Label     Inter            600    0.6875rem (11px) uppercase  —           +0.07em
Mono Data JetBrains Mono   500    0.875rem (14px)             —           −0.02em
```

### Klíčové změny oproti současnému stavu

- **H3 přechází z Inter 600 na Space Grotesk 500** — celá heading hierarchie (Display–H3) je nyní z jednoho fontu
- **Display tracking** utažen z −0.04em na −0.05em
- **H1 tracking** utažen z −0.03em na −0.04em
- **H2** snížen z 700 na 600 a tracking z −0.02em na −0.025em
- **Label tracking** upraven z +0.06em na +0.07em
- **Mono data tracking** přidán −0.02em (dříve 0)
- Pravidlo "Syne NIKDY pod 18px" odpadá — Space Grotesk funguje dobře i na H3 (17px)

---

## CSS font tokeny

```css
/* Beze změny názvu tokenů — jen hodnota */
--eb-font-display: "Space Grotesk", system-ui, sans-serif;
--eb-font-body:    "Inter", "Segoe UI Variable Text", system-ui, sans-serif;
--eb-font-mono:    "JetBrains Mono", "Cascadia Code", monospace;
```

---

## Načítání fontů

### Google Fonts URL

```
https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap
```

Syne se přestane načítat — váhy 700 a 800 se odstraní z URL.

### Soubory k aktualizaci

| Soubor | Změna |
|--------|-------|
| `frontend/src/assets/fonts.css` | Swap Syne → Space Grotesk v Google Fonts URL |
| `backend/templates/public/base_public.html` | Swap Syne → Space Grotesk v `<link>` tagu |
| `docs/visual-style-preview.html` | Nová typografická škála + font URL |
| `docs/app-dashboard-preview.html` | Nová typografická škála + font URL |
| `docs/visual-style-guide.md` | Aktualizace font stack sekce a typografické škály |

---

## Scope — co se NEMĚNÍ

- Barevný systém (--eb-lime, --eb-blue, atd.)
- Spacing a grid
- Border radius
- Komponentní CSS (EbButton, EbCard…) — používají `font: inherit` nebo `var(--eb-font-body)`
- Veškerá Vue komponenty — nepotřebují změnu pokud používají tokeny
- Logo (wordmark zůstává Space Grotesk / byl Syne — logo soubory se neupravují dokud nebude rozhodnutí o rebrandingu)

---

## Výsledek v preview souborech

Nový visual style preview zahrnuje:
- Before/After srovnání Syne vs Space Grotesk
- Kompletní typografická škála s hodnotami
- Hero sekce simulace (landing page)
- Dashboard simulace (athlete view s týdenními tréninky, badgemi, mono daty)
- Metrické karty (JetBrains Mono v akci)
- Tlačítka a input komponenty
