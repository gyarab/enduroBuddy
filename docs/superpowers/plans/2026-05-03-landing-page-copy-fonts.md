# Landing Page Copy Rewrite + Font Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Switch fonts from self-hosted WOFF2 to Google Fonts CDN (Syne → Outfit, Nunito fixed with latin-ext), rewrite all landing page copy with authentic indie-tool voice, update about.vue copy and remove the founder quote block.

**Architecture:** Pure content/config changes — no new components, no API changes, no structural layout changes. Three layers: (1) font loading via nuxt.config.ts head links, (2) i18n JSON key updates, (3) one template line removal in about.vue.

**Tech Stack:** Nuxt 3, @nuxtjs/i18n, Google Fonts CDN (fonts.googleapis.com/css2)

---

## File Map

| File | Change |
|------|--------|
| `frontend/nuxt.config.ts` | Add `app.head.link` (preconnect + CDN stylesheet); remove `~/assets/fonts.css` from `css[]` |
| `frontend/assets/fonts.css` | Delete |
| `frontend/assets/design-tokens.css` | `--eb-font-display`: `"Syne"` → `"Outfit"` |
| `frontend/i18n/locales/cs.json` | Update landing + about keys per spec |
| `frontend/i18n/locales/en.json` | Update landing + about keys per spec |
| `frontend/pages/about.vue` | Remove `founderQuote` paragraph from template |

---

## Task 1: Google Fonts CDN + Outfit token

**Files:**
- Modify: `frontend/nuxt.config.ts`
- Modify: `frontend/assets/design-tokens.css`
- Delete: `frontend/assets/fonts.css`

- [ ] **Step 1: Update nuxt.config.ts — add CDN links, remove fonts.css**

Replace the entire `css` array and add `app.head` block. The full updated file:

```ts
import { resolve } from "path"

export default defineNuxtConfig({
  compatibilityDate: "2024-11-01",
  devtools: { enabled: true },

  components: [
    { path: "~/components", pathPrefix: false },
  ],

  modules: [
    "@pinia/nuxt",
    "@nuxtjs/i18n",
  ],

  app: {
    head: {
      link: [
        { rel: "preconnect", href: "https://fonts.googleapis.com" },
        { rel: "preconnect", href: "https://fonts.gstatic.com", crossorigin: "" },
        {
          rel: "stylesheet",
          href: "https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800&family=Nunito:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap",
        },
      ],
    },
  },

  routeRules: {
    "/": { ssr: true },
    "/about": { ssr: true },
    "/terms": { ssr: true },
    "/privacy": { ssr: true },
    "/dashboard": { ssr: false },
    "/app/**": { ssr: false },
    "/coach/**": { ssr: false },
    "/accounts/**": { ssr: false },
  },

  runtimeConfig: {
    public: {
      apiBase: "/api/v1",
      appHost: "",
    },
  },

  i18n: {
    locales: [
      { code: "cs", file: "cs.json" },
      { code: "en", file: "en.json" },
    ],
    defaultLocale: "cs",
    langDir: "locales/",
    strategy: "no_prefix",
    detectBrowserLanguage: false,
    bundle: {
      optimizeTranslationDirective: false,
    },
  },

  css: [
    "~/assets/design-tokens.css",
    "~/assets/css/public-base.css",
    "~/assets/css/public-home.css",
    "~/assets/css/public-about.css",
    "~/assets/css/public-legal.css",
  ],

  alias: {
    "@": resolve(__dirname, "./"),
  },

  vite: {
    server: {
      proxy: {
        "/api": "http://localhost:8000",
        "/admin": "http://localhost:8000",
        "/accounts/google": "http://localhost:8000",
        "/i18n/set_language": "http://localhost:8000",
        "/static": "http://localhost:8000",
      },
    },
  },
})
```

- [ ] **Step 2: Update design-tokens.css — Syne → Outfit**

In `frontend/assets/design-tokens.css` line 30, change:
```css
--eb-font-display: "Syne", system-ui, sans-serif;
```
to:
```css
--eb-font-display: "Outfit", system-ui, sans-serif;
```

- [ ] **Step 3: Delete fonts.css**

```bash
git rm frontend/assets/fonts.css
```

- [ ] **Step 4: Run tests to confirm nothing broke**

```bash
cd frontend && npm test
```

Expected: all tests pass (copy changes don't affect tests; font token change is CSS-only).

- [ ] **Step 5: Visual check — open dev server**

```bash
cd frontend && npm run dev
```

Open http://localhost:3000 in browser. Verify:
- Nadpisy jsou v Outfitu (geometrická, ne kulatá/Syne)
- Czech text (ě, š, č, ř, ž, á, í, é) se renderuje správně — bez fallbacku na systémový font
- Nunito body text vypadá stejně jako dřív (jen teď s diakritikou)

- [ ] **Step 6: Commit**

```bash
cd .. && git add frontend/nuxt.config.ts frontend/assets/design-tokens.css && git commit -m "feat(fonts): Google Fonts CDN — Outfit display, Nunito+JetBrains with latin-ext"
```

---

## Task 2: cs.json — landing page copy

**Files:**
- Modify: `frontend/i18n/locales/cs.json`

Všechny klíče jsou uvnitř `"landing": { ... }` objektu (přibližně řádky 360–436).

- [ ] **Step 1: Update hero keys**

```json
"eyebrow": "Tréninkový workspace",
"h1": "Konec tabulek.\nPlán a realita\nna jednom místě.",
"subtitle": "Trénoval jsem a potřeboval jsem fungující systém pro spolupráci s trenérem. Žádný existující nástroj nestačil — tak jsem postavil vlastní. Měsíční plány, splněné tréninky a Garmin aktivity v jednom workspace.",
```

- [ ] **Step 2: Update features section keys**

```json
"featuresTitle": "Navrženo pro jednu věc.",
"featuresLead": "Vidět plán a realitu vedle sebe. Bez zbytečností.",
"feature1Copy": "Postav měsíc, rozlož zátěž po týdnech. Každý sportovec vidí svůj plán okamžitě — ne dokument, ale živá data.",
"feature2Copy": "Plánované kilometry vedle splněných. Okamžitě vidíš, kde se plán a realita rozcházejí.",
"feature3Copy": "Sportovec propojí Garmin účet. Aktivity se synchronizují automaticky — žádné ruční přepisování.",
"feature4Copy": "Stáhni FIT soubor z libovolného GPS zařízení a importuj jedním klikem. Funguje s čímkoli.",
"feature5Copy": "Více sportovců, jeden plán. Organizuj skupiny, posílej pozvánky, sdílej strukturu hromadně.",
"feature6Copy": "Všichni svěřenci na jednom místě. Kdo plní, kdo zaostává — bez otevírání každého profilu.",
```

- [ ] **Step 3: Update How It Works keys**

```json
"step2Copy": "Sportovci se připojí přes coach code nebo skupinovou pozvánku. Plán vidí okamžitě.",
"step3Copy": "Sportovci zapisují tréninky a synchronizují Garmin aktivity. Vidíš plnění v reálném čase.",
"coachBullet4": "Vidí rozdíl mezi plánem a realitou okamžitě",
"athleteBullet1": "Vidí plán den po dni bez zbytečných kliků",
"athleteBullet4": "Páruje plán se skutečností automaticky",
```

- [ ] **Step 4: Update Audience + CTA keys**

```json
"audienceTitle": "Pro ty, kdo to s tréninkem myslí vážně.",
"audienceLead": "Ať trénuješ sám nebo vedeš skupinu — EnduroBuddy se přizpůsobí.",
"audience1Copy": "Běžečtí, cyklistití i triatlonoví koučové, kteří potřebují přehled bez zbytečné složitosti.",
"audience2Copy": "Atleti, kteří chtějí plán a výsledky na jednom místě — ne rozptýlená data v pěti aplikacích.",
"audience3Copy": "Skupiny a týmy, které potřebují sdílet plány a sledovat plnění najednou.",
"ctaHeading": "Zkus to. Je to zdarma.",
"ctaSub": "Bez platební karty. Bez závazků.",
```

- [ ] **Step 5: Commit**

```bash
git add frontend/i18n/locales/cs.json && git commit -m "feat(copy): cs.json — landing page rewrite, autentický indie tón"
```

---

## Task 3: en.json — landing page copy

**Files:**
- Modify: `frontend/i18n/locales/en.json`

Stejná struktura jako cs.json, všechny klíče uvnitř `"landing": { ... }`.

- [ ] **Step 1: Update hero keys**

```json
"eyebrow": "Training workspace",
"h1": "No more spreadsheets.\nPlan and reality\nin one place.",
"subtitle": "I trained and needed a working system for coach collaboration. No existing tool was good enough — so I built my own. Monthly plans, completed sessions and Garmin activities in one workspace.",
```

- [ ] **Step 2: Update features section keys**

```json
"featuresTitle": "Built for one thing.",
"featuresLead": "See plan and reality side by side. Nothing extra.",
"feature1Copy": "Build the month, distribute load across weeks. Every athlete sees their plan instantly — not a document, but live data.",
"feature2Copy": "Planned kilometres next to completed ones. See immediately where plan and reality diverge.",
"feature3Copy": "The athlete connects their Garmin account. Activities sync automatically — no manual transcription.",
"feature4Copy": "Download a FIT file from any GPS device and import with one click. Works with anything.",
"feature5Copy": "Multiple athletes, one plan. Organise groups, send invites, share structure at scale.",
"feature6Copy": "All athletes in one view. Who's on track, who's behind — without opening every profile.",
```

- [ ] **Step 3: Update How It Works keys**

```json
"step2Copy": "Athletes join via coach code or group invite. They see their plan immediately.",
"step3Copy": "Athletes log sessions and sync Garmin activities. You see completion in real time.",
"coachBullet4": "See the gap between plan and reality immediately",
"athleteBullet1": "See the plan day by day without unnecessary clicks",
"athleteBullet4": "Matches plan with reality automatically",
```

- [ ] **Step 4: Update Audience + CTA keys**

```json
"audienceTitle": "For those who take training seriously.",
"audienceLead": "Whether you train alone or coach a group — EnduroBuddy adapts.",
"audience1Copy": "Running, cycling and triathlon coaches who need oversight without unnecessary complexity.",
"audience2Copy": "Athletes who want plan and results in one place — not scattered data across five apps.",
"audience3Copy": "Groups and teams that need to share plans and track completion at once.",
"ctaHeading": "Try it. It's free.",
"ctaSub": "No credit card. No commitment.",
```

- [ ] **Step 5: Commit**

```bash
git add frontend/i18n/locales/en.json && git commit -m "feat(copy): en.json — landing page rewrite"
```

---

## Task 4: About page — copy + remove founder quote

**Files:**
- Modify: `frontend/i18n/locales/cs.json`
- Modify: `frontend/i18n/locales/en.json`
- Modify: `frontend/pages/about.vue`

- [ ] **Step 1: Update about keys in cs.json**

Klíče jsou uvnitř `"about": { ... }` objektu (přibližně řádky 438–456):

```json
"lead": "EnduroBuddy vznikl z reálné potřeby: chtěl jsem fungující systém pro plánování tréninků se svým trenérem. Žádný existující nástroj nepracoval tak jak jsem chtěl — tak jsem napsal vlastní, pořádně.",
"storyP1": "Trénoval jsem a plánoval tréninky s trenérem. Plán chodil v PDF nebo Excelu, výsledky šly zpátky mailem, aktivity z Garminu byly jinde. Každý týden ruční synchronizace dat, která by měla být automatická.",
"storyP2": "Existující nástroje jako TrainingPeaks fungují dobře, ale jsou navržené pro jiný typ spolupráce. Chtěl jsem jednoduchý workspace: trenér plánuje, sportovec plní, oba vidí totéž. Nic navíc.",
"storyP3": "EnduroBuddy jsem začal psát jako projekt pro vlastní potřebu. Postupně se z toho stala pořádná aplikace — s Garmin integrací, FIT importem, tréninkovými skupinami a živým porovnáváním plánu s realitou.",
```

Klíč `"founderQuote"` **smazat** z cs.json.

- [ ] **Step 2: Update about keys in en.json**

```json
"lead": "EnduroBuddy was born from a real need: I wanted a working system for planning training with my coach. No existing tool worked the way I wanted — so I wrote my own, properly.",
"storyP1": "I trained and planned sessions with my coach. The plan came as a PDF or spreadsheet, results went back by email, Garmin activities were elsewhere. Every week, manual syncing of data that should be automatic.",
"storyP2": "Existing tools like TrainingPeaks work well, but are designed for a different type of collaboration. I wanted a simple workspace: coach plans, athlete executes, both see the same thing. Nothing extra.",
"storyP3": "I started writing EnduroBuddy as a project for my own use. It gradually became a proper application — with Garmin integration, FIT import, training groups and live plan vs. reality comparison.",
```

Klíč `"founderQuote"` **smazat** z en.json.

- [ ] **Step 3: Remove founderQuote from about.vue**

V `frontend/pages/about.vue` smazat řádek 37:
```html
<p class="eb-about-founder-quote">"{{ t("about.founderQuote") }}"</p>
```

Výsledná founder sekce (řádky 32–39):
```html
<div class="eb-about-founder">
  <div class="eb-about-avatar" aria-hidden="true">VH</div>
  <div>
    <div class="eb-about-founder-name">{{ t("about.founderName") }}</div>
    <div class="eb-about-founder-role">{{ t("about.founderRole") }}</div>
  </div>
</div>
```

- [ ] **Step 4: Run tests**

```bash
cd frontend && npm test
```

Expected: all tests pass.

- [ ] **Step 5: Visual check — about page**

```bash
npm run dev
```

Otevři http://localhost:3000/about. Ověř:
- Nové texty (storyP1–P3, lead) jsou viditelné
- Founder sekce zobrazuje jen jméno + roli (žádný citát)
- Czech diakritika se renderuje správně v Outfitu i Nunitu

- [ ] **Step 6: Commit**

```bash
cd .. && git add frontend/i18n/locales/cs.json frontend/i18n/locales/en.json frontend/pages/about.vue && git commit -m "feat(copy): about page rewrite + remove founder quote"
```
