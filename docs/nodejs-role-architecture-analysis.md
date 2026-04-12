# Role Node.js v projektu EnduroBuddy

Datum analýzy: 2026-04-10

## Krátká odpověď

Node.js tady nemá roli aplikačního backendu. Backend aplikace je Django: řeší auth, session, CSRF, API, business logiku, databázi a servírování HTML entrypointu pro přihlášenou část.

Node.js je v tomto projektu vývojový a buildovací toolchain pro Vue SPA:

- spouští Vite dev server s hot reloadem,
- kompiluje Vue Single File Components a TypeScript do browserového JavaScriptu/CSS,
- spouští frontendové testy přes Vitest,
- spravuje npm závislosti jako Vue, Pinia, Vue Router, Axios a vývojové nástroje.

Tvoje intuice je tedy z velké části správná: výsledkem SPA je statický JS/CSS/HTML běžící v prohlížeči a produkční server nemusí být Node.js. Zároveň ale moderní Vue 3 + TypeScript + Vite workflow prakticky předpokládá Node.js v build/dev fázi.

## Co jsem v kódu našel

### Frontend toolchain

Soubor `frontend/package.json` definuje samostatný npm projekt:

- `npm run dev` -> `vite`
- `npm run build` -> `vite build`
- `npm test` -> `vitest`
- `npm run typecheck` -> `vue-tsc --noEmit`

Runtime frontendové závislosti jsou:

- `vue`
- `vue-router`
- `pinia`
- `axios`

Vývojové závislosti jsou mimo jiné:

- `vite`
- `@vitejs/plugin-vue`
- `typescript`
- `vitest`
- `vue-tsc`
- `jsdom`
- `@vue/test-utils`

To znamená, že Node.js je nutný pro vývoj, build, typecheck a frontend testy. Není nutný k obsluze HTTP requestů v produkční aplikaci.

### Vite konfigurace

`frontend/vite.config.ts` nastavuje:

- dev server na `0.0.0.0:5173`,
- proxy na Django `127.0.0.1:8000` pro `/api`, `/accounts`, `/app`, `/coach`, `/static`,
- build output do `../backend/static_build/spa`,
- hlavní entry soubor jako `app.js`,
- CSS assety jako `app.css`,
- chunks do `chunks/[name].js`.

Import `node:url` ve Vite/Vitest konfiguraci je jen použití Node built-in API uvnitř konfiguračního souboru. Není to žádná Node část produkční aplikace.

### Django SPA entrypoint

`backend/config/urls.py` směruje:

- `/api/v1/` na Django API,
- `/accounts/` na allauth,
- `/app/*` a `/coach/*` na `spa_entry`,
- veřejné stránky jako `/`, `/about/`, `/terms/`, `/privacy/` na Django templates.

`backend/config/views_spa.py` renderuje `backend/templates/spa.html`.

`backend/templates/spa.html` se chová podle `settings.DEBUG`:

- v debug režimu načítá `{{ spa_vite_dev_server_url }}/@vite/client` a `{{ spa_vite_dev_server_url }}/src/main.ts`,
- mimo debug režim načítá statické soubory přes Django `{% static %}`: `spa/app.css` a `spa/app.js`.

To je klasický model: při vývoji běží Vite přes Node.js kvůli rychlé zpětné vazbě; v produkci Django/Whitenoise servíruje hotové statické assety.

### Django nastavení statických souborů

`backend/config/settings.py` obsahuje:

- `STATICFILES_DIRS = [BASE_DIR / "static", BASE_DIR / "static_build"]`
- `STATIC_ROOT = BASE_DIR / "staticfiles"`
- Whitenoise storage pro produkční statické soubory.

Tím se Vite build z `backend/static_build/spa` dostane do Django staticfiles systému.

### Docker

Aktuální `Dockerfile` je čistě Python/Django image:

- začíná z `python:3.12-slim`,
- instaluje Python requirements,
- kopíruje jen `backend`,
- spouští migrace, `collectstatic` a Gunicorn.

Neobsahuje Node.js build stage a nekopíruje `frontend/`.

`docker-compose.yml` a `docker-compose.prod.yml` také nespouští separátní frontend/Vite service. Compose spouští Django web a PostgreSQL.

Praktický důsledek:

- produkční image sama neumí vytvořit Vue build,
- spoléhá na to, že `backend/static_build/spa` už existuje před buildem image,
- v dev režimu `DEBUG=true` bude `/app/` a `/coach/` očekávat Vite dev server na `localhost:5173`; pokud běží jen Django přes compose bez Vite, SPA entrypoint bude odkazovat na server, který nemusí existovat.

### Stav build artifactů

`backend/static_build/spa` je v gitu sledovaný, například:

- `backend/static_build/spa/app.js`
- `backend/static_build/spa/app.css`
- `backend/static_build/spa/chunks/AthleteView.js`
- `backend/static_build/spa/chunks/CoachView.js`

Zároveň `CLAUDE.md` tvrdí, že `backend/static_build/` je generovaný a není v gitu. To neodpovídá aktuálnímu stavu repozitáře.

V `.gitignore` je ignorováno `frontend/node_modules/`, `frontend/dist/`, `frontend/.vite/`, ale není ignorováno `backend/static_build/`. Proto jsou Vite build assety aktuálně verzované.

## Je Node.js pro SPA a Vue nutný?

V absolutním smyslu ne. Browser nakonec dostane JS/CSS/HTML a vykoná ho sám. Teoreticky by šlo:

- psát čistý JavaScript bez buildu,
- použít Vue přes CDN,
- nepoužívat TypeScript ani `.vue` Single File Components,
- nepoužívat Vite, bundling, HMR a Vitest.

To ale znamená vzdát se většiny benefitů, kvůli kterým se Vue SPA v projektu zavedla: komponenty, TypeScript, rychlý vývoj, modulární importy, testy, build optimalizace a stabilní správa npm závislostí.

Pro aplikaci této velikosti je Node.js jako frontend toolchain best practice. Není best practice provozovat kvůli tomu Node.js jako druhý produkční backend, pokud Django může bezpečně servírovat statické assety. Tady to projekt právě dělá: Node má být build/dev nástroj, Django má zůstat runtime server.

## Srovnání s best practice

### Co je v pořádku

Oddělení odpovědností je smysluplné:

- Django: server, auth, session, CSRF, API, public templates, staticfiles.
- Vue SPA: přihlášené aplikační UI pod `/app/*` a `/coach/*`.
- Node/Vite: lokální frontend vývoj a build.

Session-based auth s Axios `withCredentials` a CSRF cookie je pro Django + same-origin SPA konzervativní a rozumný přístup. Není zbytečně zaveden JWT/tokenový auth model.

Produkční servírování statických assetů přes Django/Whitenoise je pro menší až střední aplikaci přijatelné. Alternativou by byl Nginx/CDN, ale není nutné kvůli samotnému Node.js.

Vite dev server s proxy na Django je standardní lokální workflow, protože dává HMR a přitom API zůstává v Django.

### Co je architektonicky neuhlazené

1. Produkční Docker build neobsahuje frontend build krok.

   Pokud se má image dát spolehlivě postavit z čistého checkoutu, měl by Dockerfile nebo CI pipeline spouštět `npm ci && npm run build` a výsledky vložit do Django staticfiles. Aktuální stav spoléhá na předem existující `backend/static_build/spa`.

2. Dev compose neobsahuje Vite frontend service.

   `DEBUG=true` v `spa.html` znamená, že Django bude pro SPA načítat skripty z Vite serveru. `docker-compose.yml` ale spouští jen `db` a `web`. Vývojář tak musí ručně spustit `npm run dev` mimo compose, jinak SPA část nebude kompletní.

3. Dokumentace je částečně rozjetá.

   `CLAUDE.md` popisuje Vue/Vite architekturu aktuálněji než `README.md`. README pořád mluví o server-rendered frontendu s vlastním JS/CSS a v rychlém startu nezmiňuje Node/Vite workflow. To může vést přesně k té otázce, kterou pokládáš: proč tu Node vůbec je?

4. Build artifacty jsou verzované, ale dokumentace tvrdí opak.

   Pokud má být `backend/static_build/` generované a neverzované, mělo by být v `.gitignore` a produkční build by ho měl generovat. Pokud má být naopak záměrně verzované, dokumentace by to měla říct jako vědomé rozhodnutí. Teď je to napůl.

5. Vite konfigurace pojmenovává všechny CSS assety jako `app.css`.

   V repozitáři jsou ale vedle `app.css` i starší `app2.css`, `app3.css`, ... `app6.css`. To naznačuje historické nebo stale build výstupy. Není to samo o sobě důkaz chyby v runtime, ale je to signál, že build output adresář není spravovaný čistě.

6. Produkční `Dockerfile` kopíruje jen `backend`.

   To je v pořádku jen tehdy, pokud se frontend build commitoval nebo generoval před docker buildem. Jako best practice bych preferoval buď explicitní CI artifact, nebo multi-stage Docker build.

## Doporučený cílový model

Za nejčistší architekturu pro tento projekt považuji:

1. Django zůstane jediný produkční runtime backend.

   Není důvod přidávat Node.js server pro produkci, pokud SPA běží jako statické assety a API je v Django.

2. Node.js bude povinný pouze pro vývoj, testy a build.

   Lokálně:

   ```bash
   cd frontend
   npm ci
   npm run dev
   ```

   Vedle toho běží Django:

   ```bash
   cd backend
   python manage.py runserver
   ```

3. Produkční build by měl být reprodukovatelný z čistého checkoutu.

   Doporučená varianta je multi-stage Dockerfile:

   ```dockerfile
   FROM node:20-alpine AS frontend-build
   WORKDIR /app/frontend
   COPY frontend/package*.json ./
   RUN npm ci
   COPY frontend/ ./
   RUN npm run build

   FROM python:3.12-slim
   ...
   COPY backend ./backend
   COPY --from=frontend-build /app/backend/static_build ./backend/static_build
   ```

   Přesná cesta by se musela sladit s tím, že současný Vite `outDir` míří na `../backend/static_build/spa`.

4. Dev compose by měl buď obsahovat frontend service, nebo dokumentace musí říct, že Vite běží mimo compose.

   Varianta s compose service:

   ```yaml
   frontend:
     image: node:20-alpine
     working_dir: /app/frontend
     command: sh -c "npm ci && npm run dev -- --host 0.0.0.0"
     volumes:
       - ./frontend:/app/frontend
     ports:
       - "5173:5173"
   ```

5. Rozhodnout, jestli `backend/static_build/spa` verzovat.

   Doporučení:

   - pokud deployment běží z Docker image/CI: neverzovat build output, generovat při buildu,
   - pokud deployment probíhá ručním kopírováním na server bez Node.js: verzování build outputu může být pragmatický kompromis, ale mělo by být jasně dokumentované.

   Z hlediska best practice je čistší generovat build artifact v CI/Docker buildu a necommitovat ho.

## Odpověď na otázku „k čemu je Node.js tady dobré?“

Node.js je tady dobré k tomu, aby se moderní Vue aplikace dala rozumně vyvíjet, testovat a sestavit:

- převádí `.vue` komponenty a TypeScript na browser-compatible JS,
- poskytuje Vite dev server s hot reloadem,
- spravuje npm balíčky a lockfile,
- spouští Vitest a Vue test utils,
- generuje produkční statické assety, které pak může servírovat Django.

Není tady dobré jako druhý backend a podle kódu se tak ani nepoužívá. Pokud někdo říká „aplikace potřebuje Node.js v produkci“, tak podle aktuální architektury je to nepřesné. Přesnější je: „projekt potřebuje Node.js v build pipeline a pro frontend vývoj; produkční runtime je Django.“

## Shrnutí hodnocení

Architektonický směr je správný: Django jako backend a Vue SPA jako frontend pro přihlášenou část je běžný a zdravý model. Použití Node.js pro Vite/Vue toolchain je best practice, ne známka špatného rozdělení backendu.

Slabina není samotná existence Node.js, ale nedotažené provozní ohraničení jeho role. Repozitář by měl jasně říct a technicky vynutit, zda se frontend build generuje v Docker/CI, nebo se commitují hotové soubory v `backend/static_build/spa`. Teď projekt stojí mezi oběma světy, což zbytečně zvyšuje kognitivní i deployment riziko.
