# Landing Page: Copy Rewrite + Font Fix

**Datum:** 2026-05-03  
**Větev:** main  
**Rozsah:** `frontend/` — fonty, i18n copy (cs + en), about.vue struktura

---

## Kontext

Cíl: finalizovat landing page před žádostí o oficiální Garmin Connect API. Dvě kategorie změn:

1. **Fonty** — self-hosted WOFF2 soubory jsou stažené bez `latin-ext` subsetu, česká diakritika proto padá na systémové fonty.
2. **Copy** — přepsat všechny texty s jasným marketingovým hlasem: autentický indie nástroj, konkrétní výhody, bez generických SaaS frází.

Žádný Garmin-API-specifický obsah na stránkách — to bude řešeno přímo v API žádosti.

---

## Fonty

### Volba

| Role | Starý font | Nový font | Důvod |
|------|-----------|-----------|-------|
| Display (nadpisy, hero) | Syne | **Outfit** | Geometrická, moderní, stejná energie — plná podpora latin-ext |
| Body (UI, texty) | Nunito | **Nunito s latin-ext** | Zachovat současný vzhled, jen opravit WOFF2 soubory |
| Mono (data, čísla) | JetBrains Mono | JetBrains Mono (beze změny) | Pro číselná data se diakritika nepoužívá |

### Co se mění

Fonty se načítají z **Google Fonts CDN** — žádné lokální soubory, žádné WOFF2 v `backend/static/fonts/`.

Google Fonts v2 (`fonts.googleapis.com/css2`) automaticky servíruje správné unicode-range subsets (latin + latin-ext) podle potřeby prohlížeče — czech diacritics jsou pokryty automaticky.

**CDN URL:**
```
https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800&family=Nunito:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap
```

**Integrace v Nuxt:**
- `nuxt.config.ts` — přidat `app.head.link` s `preconnect` pro `fonts.googleapis.com` + `fonts.gstatic.com` a `stylesheet` link na CDN URL výše
- `frontend/assets/fonts.css` — **smazat celý soubor** (všechny `@font-face` deklarace nahrazuje CDN)
- `nuxt.config.ts` `css` pole — odebrat `~/assets/fonts.css`
- `frontend/assets/design-tokens.css` — `--eb-font-display: 'Outfit', sans-serif`
- Všechny komponenty které používají `font-family: 'Syne'` nebo `var(--eb-font-display)` jsou pokryty přes token, žádné ruční změny v komponentách.

**Existující lokální font soubory** (`backend/static/fonts/*.woff2`) zůstanou na disku — neodstraňujeme, mohly by být potřeba pro SPA offline nebo budoucí self-hosting. Prostě přestanou být referencované.

---

## Copy — Landing Page (`index.vue`)

Tón: **autentický indie nástroj** — "Měl jsem reálnou potřebu, žádný nástroj mi nestačil, tak jsem postavil vlastní."  
Jazyk: konkrétní výhody, žádné generické SaaS fráze, kratší věty.

### Hero

| Klíč | Česky | Anglicky |
|------|-------|----------|
| `eyebrow` | Tréninkový workspace | Training workspace |
| `h1` | Konec tabulek.\nPlán a realita\nna jednom místě. | No more spreadsheets.\nPlan and reality\nin one place. |
| `subtitle` | Trénoval jsem a potřeboval jsem fungující systém pro spolupráci s trenérem. Žádný existující nástroj nestačil — tak jsem postavil vlastní. Měsíční plány, splněné tréninky a Garmin aktivity v jednom workspace. | I trained and needed a working system for coach collaboration. No existing tool was good enough — so I built my own. Monthly plans, completed sessions and Garmin activities in one workspace. |

### Features sekce

| Klíč | Česky | Anglicky |
|------|-------|----------|
| `featuresTitle` | Navrženo pro jednu věc. | Built for one thing. |
| `featuresLead` | Vidět plán a realitu vedle sebe. Bez zbytečností. | See plan and reality side by side. Nothing extra. |
| `feature1Copy` | Postav měsíc, rozlož zátěž po týdnech. Každý sportovec vidí svůj plán okamžitě — ne dokument, ale živá data. | Build the month, distribute load across weeks. Every athlete sees their plan instantly — not a document, but live data. |
| `feature2Copy` | Plánované kilometry vedle splněných. Okamžitě vidíš, kde se plán a realita rozcházejí. | Planned kilometres next to completed ones. See immediately where plan and reality diverge. |
| `feature3Copy` | Sportovec propojí Garmin účet. Aktivity se synchronizují automaticky — žádné ruční přepisování. | The athlete connects their Garmin account. Activities sync automatically — no manual transcription. |
| `feature4Copy` | Stáhni FIT soubor z libovolného GPS zařízení a importuj jedním klikem. Funguje s čímkoli. | Download a FIT file from any GPS device and import with one click. Works with anything. |
| `feature5Copy` | Více sportovců, jeden plán. Organizuj skupiny, posílej pozvánky, sdílej strukturu hromadně. | Multiple athletes, one plan. Organise groups, send invites, share structure at scale. |
| `feature6Copy` | Všichni svěřenci na jednom místě. Kdo plní, kdo zaostává — bez otevírání každého profilu. | All athletes in one view. Who's on track, who's behind — without opening every profile. |

### How It Works

Kroky — jen upřesnění formulace:

| Klíč | Česky | Anglicky |
|------|-------|----------|
| `step2Copy` | Sportovci se připojí přes coach code nebo skupinovou pozvánku. Plán vidí okamžitě. | Athletes join via coach code or group invite. They see their plan immediately. |
| `step3Copy` | Sportovci zapisují tréninky a synchronizují Garmin aktivity. Vidíš plnění v reálném čase. | Athletes log sessions and sync Garmin activities. You see completion in real time. |
| `coachBullet4` | Vidí rozdíl mezi plánem a realitou okamžitě | See the gap between plan and reality immediately |
| `athleteBullet1` | Vidí plán den po dni bez zbytečných kliků | See the plan day by day without unnecessary clicks |
| `athleteBullet4` | Páruje plán se skutečností automaticky | Matches plan with reality automatically |

### Audience sekce

| Klíč | Česky | Anglicky |
|------|-------|----------|
| `audienceTitle` | Pro ty, kdo to s tréninkem myslí vážně. | For those who take training seriously. |
| `audienceLead` | Ať trénuješ sám nebo vedeš skupinu — EnduroBuddy se přizpůsobí. | Whether you train alone or coach a group — EnduroBuddy adapts. |
| `audience1Copy` | Běžečtí, cyklistití i triatlonoví koučové, kteří potřebují přehled bez zbytečné složitosti. | Running, cycling and triathlon coaches who need oversight without unnecessary complexity. |
| `audience2Copy` | Atleti, kteří chtějí plán a výsledky na jednom místě — ne rozptýlená data v pěti aplikacích. | Athletes who want plan and results in one place — not scattered data across five apps. |
| `audience3Copy` | Skupiny a týmy, které potřebují sdílet plány a sledovat plnění najednou. | Groups and teams that need to share plans and track completion at once. |

### CTA sekce

| Klíč | Česky | Anglicky |
|------|-------|----------|
| `ctaHeading` | Zkus to. Je to zdarma. | Try it. It's free. |
| `ctaSub` | Bez platební karty. Bez závazků. | No credit card. No commitment. |

---

## Copy — About Page (`about.vue`)

### Změny

| Klíč | Česky | Anglicky |
|------|-------|----------|
| `lead` | EnduroBuddy vznikl z reálné potřeby: chtěl jsem fungující systém pro plánování tréninků se svým trenérem. Žádný existující nástroj nepracoval tak jak jsem chtěl — tak jsem napsal vlastní, pořádně. | EnduroBuddy was born from a real need: I wanted a working system for planning training with my coach. No existing tool worked the way I wanted — so I wrote my own, properly. |
| `storyP1` | Trénoval jsem a plánoval tréninky s trenérem. Plán chodil v PDF nebo Excelu, výsledky šly zpátky mailem, aktivity z Garminu byly jinde. Každý týden ruční synchronizace dat, která by měla být automatická. | I trained and planned sessions with my coach. The plan came as a PDF or spreadsheet, results went back by email, Garmin activities were elsewhere. Every week, manual syncing of data that should be automatic. |
| `storyP2` | Existující nástroje jako TrainingPeaks fungují dobře, ale jsou navržené pro jiný typ spolupráce. Chtěl jsem jednoduchý workspace: trenér plánuje, sportovec plní, oba vidí totéž. Nic navíc. | Existing tools like TrainingPeaks work well, but are designed for a different type of collaboration. I wanted a simple workspace: coach plans, athlete executes, both see the same thing. Nothing extra. |
| `storyP3` | EnduroBuddy jsem začal psát jako projekt pro vlastní potřebu. Postupně se z toho stala pořádná aplikace — s Garmin integrací, FIT importem, tréninkovými skupinami a živým porovnáváním plánu s realitou. | I started writing EnduroBuddy as a project for my own use. It gradually became a proper application — with Garmin integration, FIT import, training groups and live plan vs. reality comparison. |

### Founder sekce

Citát (`founderQuote`) se **odstraňuje** — ve Vue komponentě i v obou locale souborech.  
Zůstane pouze `founderName` + `founderRole`. Sekce se zobrazí jako jméno + role bez quote bloku.

---

## Rozsah změn — soubory

| Soubor | Změna |
|--------|-------|
| `nuxt.config.ts` | Přidat `app.head.link` — preconnect + Google Fonts CDN stylesheet; odebrat `~/assets/fonts.css` z `css` pole |
| `frontend/assets/fonts.css` | **Smazat** — nahrazeno CDN |
| `frontend/assets/design-tokens.css` | `--eb-font-display: 'Outfit', sans-serif` (bylo `'Syne'`) |
| `frontend/i18n/locales/cs.json` | Klíče dle tabulek výše |
| `frontend/i18n/locales/en.json` | Klíče dle tabulek výše |
| `frontend/pages/about.vue` | Odstranit `founderQuote` blok z template |

---

## Co se nemění

- Struktura sekce landing page (pořadí, počet sekcí) — beze změny
- Mockup v hero sekci — beze změny
- Klíče které nejsou v tabulkách výše — beze změny (stávající text je dostačující)
- Žádná nová sekce na landing page
- `about.vue` layout — beze změny kromě odebrání quote bloku
- Testy — copy změny testy neovlivní (komponenty používají `t()` klíče, ne hardcoded texty)
