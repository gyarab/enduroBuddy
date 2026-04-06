# Logo Redesign — Design Spec

**Datum:** 2026-04-06
**Status:** Schváleno uživatelem

---

## Přehled

Redesign celého logo systému EnduroBuddy. Nový mark se jmenuje **Velocity Bars** — tři vertikální obdélníky rostoucí výšky, zkosené doprava (-9°), s gradientní opacitou. Nahrazuje stávající ECG pulse mark.

---

## Koncept: Velocity Bars

Tři vertikální sloupy znázorňují stupňující se intenzitu nebo tréninkové zóny — čteno zleva doprava jako "nabíhající výkon." Zkosení -9° přidává dynamiku a pohyb vpřed. Gradientní opacity (0.38 → 0.68 → 1.0) vytváří vizuální hloubku bez dalších barev.

**Symbolizuje:**
- Stupňující se tréninkovou intenzitu (zóny 1–3)
- Progres a sílu — klíčové hodnoty endurance tréninku
- Data a precision — tři diskrétní hodnoty jako vizualizace

---

## Geometrie marku

Viewbox: `48×48px`

| Bar | x  | y  | width | height | rx  | opacity | transform     |
|-----|----|----|-------|--------|-----|---------|---------------|
| 1   | 6  | 33 | 9     | 10     | 2.5 | 0.38    | skewX(-9)     |
| 2   | 19 | 25 | 9     | 18     | 2.5 | 0.68    | skewX(-9)     |
| 3   | 32 | 14 | 9     | 29     | 2.5 | 1.0     | skewX(-9)     |

Výškový poměr: ~1 : 1.8 : 2.9

---

## Glow efekt

SVG filter aplikovaný na skupinu barů:

```xml
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
  <feGaussianBlur in="SourceGraphic" stdDeviation="2.2" result="blur"/>
  <feMerge>
    <feMergeNode in="blur"/>
    <feMergeNode in="SourceGraphic"/>
  </feMerge>
</filter>
```

**Pravidlo:** Glow se aplikuje pouze na velikostech ≥ 20px. Na 16px (favicon kontext) se glow vynechává — čitelnost má přednost.

---

## Barevné varianty

### Primární (tmavé pozadí)
- Bary: `#c8ff00` s výše uvedenými opacitami
- Glow: ano (≥ 20px)

### Inverzní (lime nebo bílé pozadí)
- Bary: `#09090b` se stejnými opacitami (0.38 / 0.68 / 1.0)
- Glow: ne

---

## Wordmark

- Font: **Syne 700**
- Text: `EnduroBuddy` (camelCase, jedno slovo)
- Barva: `#fafafa` na tmavém pozadí, `#09090b` na světlém
- Letter-spacing: `-0.03em` (velké použití), `-0.02em` (malé použití)

---

## Logo varianty — soubory k vytvoření

| Soubor | Obsah | Viewbox |
|--------|-------|---------|
| `eb-mark.svg` | Pouze mark (velocity bars + glow) | 48×48 |
| `eb-logo-full.svg` | Mark (40px) + wordmark "EnduroBuddy" | 320×48 |
| `eb-logo-compact.svg` | Mark (28px) + monogram "EB" (Syne 800) | 140×48 |
| `eb-wordmark.svg` | Pouze wordmark (Syne 700) | 240×48 |
| `eb-social-dark.svg` | Mark na tmavém pozadí, čtvercový formát | 400×400 |
| `eb-social-lime.svg` | Mark inverzní na lime pozadí, čtvercový formát | 400×400 |
| `eb-social-dark-rounded.svg` | Stejné jako dark, navíc `rx="80"` na wrapper rect | 400×400 |
| `eb-social-github.svg` | Mark na tmavém pozadí, kruhový clip-path (safe zone pro GitHub) | 400×400 |
| `eb-social-banner.svg` | Mark + wordmark na tmavém pozadí, landscape formát | 1200×630 |

Všechny soubory jdou do `backend/static/brand/` — přepisují stávající soubory.

---

## Použití v templates

### Navbar (desktop, ≥ 768px)
```html
<img src="{% static 'brand/eb-logo-full.svg' %}" alt="EnduroBuddy" height="28">
```

### Navbar (mobil, < 768px)
```html
<img src="{% static 'brand/eb-logo-compact.svg' %}" alt="EB" height="28">
```

### Favicon
`eb-mark.svg` exportovat jako `favicon.ico` (16×16, 32×32) bez glow filtru.

---

## Safe zone

- Minimální velikost marku: **16px**
- Safe zone kolem marku = šířka jednoho baru (~⅕ celkové šířky marku)
- Mezi markem a wordmarkem: mezera rovná výšce marku × 0.3

---

## Co se nemění

- CSS tokeny, barevný systém, typografie — beze změny
- `visual-style-guide.md` — sekce Logo se aktualizuje (název konceptu + specifikace)
- Stávající `logo.png` a `biglogo.png` zůstávají jako legacy fallback

---

## Aktualizace visual-style-guide.md

Sekce `## Logo` se přepíše: název konceptu z "Stride Mark" na "Velocity Bars", přidají se technické specifikace geometrie a tabulka souborů zůstane stejná.
