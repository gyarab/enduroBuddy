# Vue Frontend Migration Continuation Plan

## Purpose

Tento dokument navazuje na:

- `docs/codex-implementation/vue-frontend/2026-04-08-vue-frontend-implementation-plan.md`
- `docs/superpowers/specs/2026-04-06-vue-frontend-migration-design.md`
- `docs/superpowers/specs/2026-04-06-vue-app-visual-design.md`

Neni to nahrada puvodniho planu. Je to closing/continuation plan pro dalsi vlnu prace po tom, co uz existuje Vue SPA, athlete dashboard, coach workspace, profile completion, i18n scaffold a test guardrails.

## Current Claude Spec Re-Read

Po znovuprocteni Claudeovych dokumentu zustavaji klicove body stejne:

- Django zustava jedinym serverem pro auth, public pages, API a deployment.
- Vue 3 + TypeScript + Vite obsluhuje prihlasenou cast `/app/*` a `/coach/*`.
- Business logika se nema prepisovat, ale obalovat API vrstvou.
- Design language "Neon Lab x Swiss Precision" ma byt first-class soucast Vue komponent.
- Athlete app ma byt plne pouzitelna ve Vue.
- Coach app ma byt plne pouzitelna ve Vue.
- Profile completion a i18n patri do zaverecne faze.
- Legacy JS/templates se maji odebirat az po funkcni nahrade ve Vue.

## Important Corrections Against Previous Audit

Tento dokument opravuje par nepresnosti ze starsi auditni sekce:

- Puvodne nebyl vystaveny `POST /api/v1/training/planned/`; C2 ho doplnila pro athlete flow.
- Puvodne nebyl vystaveny `DELETE /api/v1/training/planned/{id}/`; C2 ho doplnila pro athlete flow.
- `POST /api/v1/training/completed/` neni aktualne vystaveny v `backend/api/urls.py`.
- `DELETE /api/v1/training/completed/{id}/` neni aktualne vystaveny v `backend/api/urls.py`.
- Aktualne existuji athlete training API endpointy hlavne pro:
  - planned `POST/PATCH/DELETE`
  - completed `PATCH`
  - planned second-phase `POST/DELETE`
- Coach completed policy je uzavrena podle legacy pravidel:
  - managed athlete completed zustava read-only
  - coach muze menit jen vlastni completed plan pres API, pokud bude potreba self-plan surface

## Accepted Deviations From Claude Plan

Tyto odchylky jsou zatim prijate a nejsou samy o sobe bug:

- Nepouzivame DRF ViewSets ani dedicated `backend/api/serializers/`. Aktualni API views serializuji inline, protoze payloady obaluji existujici business logiku a jsou uz dobre testovane.
- Nepouzivame `vue-i18n`. Aktualni `useI18n` custom composable je lehci a zatim dostacuje pro CS/EN potrebu.
- Coach managed completed editace neni ve Vue povolena, protoze legacy pravidla ji zakazuji.
- Frontend SPA neni big-bang full rewrite vseho. Je implementovana po slices, coz se ukazalo stabilnejsi.

## Current Status Snapshot

Hotove nebo dobre rozjete:

- SPA bootstrap pro `/app/*` a `/coach/*`
- `auth/me`
- athlete dashboard read-only + inline editace planned/completed
- parser preview a parser unit testy
- notifications API/store/dropdown
- Garmin/FIT modal a import job status API
- coach dashboard, sidebar, focus, reorder, visibility a planned editace
- profile completion pres SPA API/view
- profile settings modal v SPA pro bezne account nastaveni
- custom i18n scaffold a locale soubory `cs.json` + `en.json`
- jazykovy switch uz synchronizuje Django session pres `/i18n/set_language/`
- frontend test suite pro parser, stores, shared rows, shell, dashboard views
- backend API smoke tests pro hlavni SPA kontrakty
- testy potvrzujici, ze `/app/dashboard` a `/coach/plans` renderuji `spa.html`

Hlavni mezery:

- Completed create/delete API a Vue surface nejsou hotove.
- Uspesne import scenare jsou testovane slabsi nez guard/error scoping.
- Legacy dashboard JS/partials jsou zmapovane, ale jeste nejsou odpojene od zbylych testu a reference vrstvy.
- Mobile UI neni znovu auditovane proti visual design specu po vsech feature slices.
- Dokumentace v nekterych starsich planech zaostava za realnym stavem implementace a musi se brat jen jako historicky snapshot.

## Continuation Phases

### Phase C1: Reality Fix And Backend Import Coverage

Status: partially completed 2026-04-09

Goal:

- Srovnat test coverage s realnymi endpointy a snizit riziko import regresi.

Tasks:

- Hotovo: pridat backend testy pro Garmin sync happy-ish path bez volani externich sluzeb:
  - active `GarminConnection`
  - `GARMIN_SYNC_ENABLED=True`
  - mock `enqueue_garmin_sync_job`
  - `POST /api/v1/imports/garmin/start/`
  - job created / duplicate active job returns `already_running`
- Hotovo: pridat backend test pro `POST /api/v1/imports/garmin/revoke/` nad active connection.
- U FIT importu testovat jen stabilni hranice:
  - missing file guard uz existuje
  - uspesny FIT import pridat jen pokud lze reuse fixture bez krehke zavislosti na binarni parser runtime
- Hotovo: aktualizovat predchozi plan, pokud zustava nepresna veta o create/delete endpointech.

Notes:

- FIT happy path zustava vedome odlozeny. Import service ma vlastni existujici specializovane testy nad FIT fixtures; API layer zatim hlida stabilni guardy a job scoping.

Verification:

- Hotovo: `.venv\Scripts\python.exe manage.py test api.tests`
- Hotovo: `.venv\Scripts\python.exe -m compileall backend\api`

### Phase C2: Training Create/Delete API Contract

Status: partially completed 2026-04-09

Goal:

- Dorovnat Claudeuv endpoint seznam pro planned/completed create/delete, ale bez nove business logiky mimo legacy pravidla.

Backend tasks:

- Hotovo: najit existujici legacy create/delete behavior pro planned/completed.
- Hotovo: legacy obecny create/delete helper neexistuje; pridany konzervativni planned-only API kontrakt:
  - `POST /api/v1/training/planned/`
  - `DELETE /api/v1/training/planned/{id}/`
- Hotovo: coach planned create/delete kontrakt:
  - `POST /api/v1/coach/training/planned/`
  - `DELETE /api/v1/coach/training/planned/{id}/`
- Hotovo: minimalni endpoint jen pro planned training nad `resolve_week_for_day`, `TrainingWeek` a `TrainingMonth`.
- Hotovo: pridat role/access kontrolu:
  - athlete muze vytvaret/mazat jen vlastni plan, pokud to odpovida dnesnim pravidlum
  - coach muze vytvaret/mazat planned pro accessible athlete, pokud to odpovida dnesnim coach flow
  - completed managed athlete zustava read-only pro coache
- Hotovo: delete guard odmita smazat planned training, pokud ma completed nebo linked activity data.
- Odlozeno: completed create/delete, protoze nema jasny low-risk legacy ekvivalent a musi respektovat import/linked activity pravidla.

Frontend tasks:

- Hotovo: rozsirit `frontend/src/api/training.ts`.
- Hotovo: rozsirit `frontend/src/api/coach.ts`.
- Hotovo: rozsirit `frontend/src/stores/training.ts` a `frontend/src/stores/coach.ts`.
- Hotovo: pridat minimalni UI surface po backend kontraktu:
  - planned create action v empty/week area
  - planned delete v expanded planned editoru
  - potvrzeni pred delete pres browser confirm jako docasny low-risk guard
- Odlozeno: completed delete UI, protoze by mohlo rozbit import/linked activity chovani.

Notes:

- `EbModal` confirm zustava polish navazujici na visual/mobile audit. Pro tento slice je prioritou API kontrakt a bezpecne chovani.

Verification:

- Hotovo: backend API tests for planned create/delete
- Hotovo: frontend focused store/component tests zustaly zelene
- Hotovo: full frontend suite `npm.cmd test -- --run` - 75 testu
- Hotovo: `npm.cmd run typecheck`
- Hotovo: `npm.cmd run build` po escalated spusteni kvuli sandbox `esbuild` EPERM

### Phase C3: Legacy Cleanup Audit

Status: completed 2026-04-09

Goal:

- Bezpecne zmapovat, co je stale potreba pro server-rendered dashboard a co uz je nahrazeno Vue.

Audit targets:

- `backend/dashboard/static/js/dashboard_editor_planned.js`
- `backend/dashboard/static/js/dashboard_editor_completed.js`
- dalsi `backend/dashboard/static/js/*.js`
- `backend/templates/dashboard/_month_cards.html`
- `backend/templates/dashboard/_completed_week_table.html`
- dashboard partialy pouzivane jen prihlasenou aplikacni casti
- `backend/dashboard/views_home.py`
- `backend/dashboard/views_coach.py`
- regression testy, ktere stale hlidaji legacy template strukturu

Output:

- Hotovo: vytvoren cleanup report v `docs/codex-implementation/vue-frontend/2026-04-09-legacy-dashboard-cleanup-audit.md`.
- Hotovo: rozdelene soubory do kategorii:
  - keep for legacy fallback
  - remove after route switch
  - remove now
  - needs manual QA
- Zjisteni: `/app/` a `/coach/*` jsou v `backend/config/urls.py` registrovane pred `include("dashboard.urls")`, takze runtime path uz obsluhuje Vue SPA.
- Zjisteni: legacy dashboard templates/static JS nejsou bezpecne pro okamzite smazani, protoze stale existuji named URL reference, legacy endpoint testy a regression testy nad template/JS strukturou.
- Dalsi doporuceny slice: route/test realignment pred fyzickym mazanim legacy UI souboru.

Non-goal:

- Nemasat legacy soubory hned, dokud neni jasne, ze routy uz opravdu pouzivaji Vue pro dany flow.

Verification:

- Hotovo: `rg` reference check pres `backend/templates`, `backend/dashboard` a URL konfiguraci
- Odlozeno: focused dashboard regression tests, protoze C3 je audit-only bez behavioral zmen; tyto testy navic stale hlidaji legacy rendered UI, ne SPA runtime
- Manual check `/app/` a `/coach/` zustava pro navazujici visual/mobile audit

### Phase C4: Visual And Mobile Audit Pass

Status: partially completed 2026-04-09

Goal:

- Dorovnat Vue UI proti aktualnimu `2026-04-06-vue-app-visual-design.md` tam, kde jsme sli zatim MVP stylem.

Checklist:

- TopNav:
  - Hotovo: 56px height pres `--eb-topnav-height`
  - Hotovo: month navigator presunut do TopNav pro athlete i coach flow
  - Hotovo: coach athlete pill pridany do TopNav podle visual specu
  - Hotovo: mobile month nav zkracuje label a schovava athlete pill
  - Hotovo: profile dropdown uz funguje jako vstup do SPA settings surface
- Coach shell:
  - sidebar width/sticky behavior
  - mobile hamburger/toggle behavior
  - active athlete visual state
- Week cards:
  - header/body separation
  - data density
  - mono metrics
- Training rows:
  - status border semantics
  - completed/missed visual hierarchy
  - second phase indentation/connector
- Inline editors:
  - mobile full-screen or near-full-screen behavior decision
  - lime glow/focus states
  - reduced-motion respect
- Profile/settings:
  - Hotovo: account settings modal v SPA
  - Hotovo: mobile-safe stacked layout v modalu
  - Hotovo: quick links na password change / logout
- Import modal:
  - progress/status layout
  - activity/job result list clarity

Verification:

- Hotovo: `npm.cmd run typecheck`
- Hotovo: focused tests `npm.cmd test -- --run src/components/layout/TopNav.test.ts src/views/dashboard/AthleteView.test.ts src/views/dashboard/CoachView.test.ts`
- Hotovo: full frontend suite `npm.cmd test -- --run` - 75 testu
- Hotovo: `npm.cmd run build` po escalated spusteni kvuli sandbox `esbuild` EPERM
- Zbyva: dalsi visual/mobile audit polozky mimo TopNav, hlavne profile dropdown spacing, coach sidebar sticky/mobile polish a inline editor mobile behavior
- manual desktop and mobile viewport QA

### Phase C5: i18n Integration Decision

Goal:

- Rozhodnout, jestli custom `useI18n` zustane finalni, a doplnit minimalni Django language sync.

Tasks:

- Pridat unit testy pro `useI18n`:
  - default locale
  - `setLocale`
  - interpolation
  - fallback key behavior
  - reset mezi testy, aby modul-level state nekontaminoval suite
- Pridat jazykovy toggle jen pokud je v UI potreba ted.
- Hotovo: toggle existuje v profile dropdown/settings surface.
- Hotovo: `useI18n` synchronizuje `document.documentElement.lang`.
- Hotovo: `useI18n` vola Django `/i18n/set_language/` pro session sync.
- Neprechazet na `vue-i18n`, dokud custom composable neni realny blocker.

Verification:

- `npm run test -- --run src/composables/useI18n.test.ts`
- `npm run typecheck`
- `npm run build`

### Phase C6: Profile Settings Surface

Goal:

- Dorovnat Claudeuv `ProfileModal.vue` / profile settings surface, ale az po C1-C5.

Tasks:

- Zmapovat existujici server-rendered profile management:
  - update name
  - change password
  - coach request by code
- Hotovo: low-risk profile fields (jmeno/prijmeni) jsou editovatelne pres SPA API.
- Hotovo: password/logout zustavaji server-rendered/allauth pres jasne odkazy ze SPA settings modal.
- Rozhodnuto: email/password/allauth flows zustavaji server-rendered, ale vstup do nich je uz z Vue shellu.

Verification:

- backend tests pro nove profile API, pokud vznikne
- component tests pro modal
- manual QA login/profile/logout flow

## Updated Priority Order

1. C1 Backend import coverage and previous-plan correction. Garmin/API guard cast je hotova; FIT happy path je odlozeny.
2. C2 Training create/delete contract, pokud je skutecne potreba pro rollout. Planned create/delete je hotovy; completed create/delete je vedome odlozeny.
3. C3 Legacy cleanup audit.
4. C4 Visual/mobile audit pass.
5. C5 i18n integration decision.
6. C6 Profile settings surface.

## Rollout Criteria For This Continuation Plan

Continuation plan bude hotovy, kdyz:

- predchozi plan uz neobsahuje zavadejici tvrzeni o create/delete endpoints
- backend import happy-path coverage je doplnena nebo vedome odlozena s duvodem
- create/delete training flow je bud implementovan, nebo explicitne odlozen mimo rollout
- existuje legacy cleanup report
- mobile/visual audit ma jasny pass/fail seznam
- i18n ma testy a rozhodnuti custom-vs-library
- `npm run typecheck`, `npm run build` a relevantni backend tests prochazeji

## How To Report After Each Slice

Po kazdem dalsim implementacnim slice porovnat:

- stav proti tomuto continuation planu
- stav proti puvodnimu Codex planu
- stav proti Claudeovu migration designu
- stav proti visual design specu, pokud se menilo UI

Pokud se objevi rozpor mezi dokumenty a kodem, aktualizovat tento continuation plan jako zdroj dalsi reality.
