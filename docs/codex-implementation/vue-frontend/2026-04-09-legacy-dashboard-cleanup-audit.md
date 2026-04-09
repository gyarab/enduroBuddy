# Legacy Dashboard Cleanup Audit

Date: 2026-04-09

## Summary

Vue SPA is already the runtime owner for the authenticated app shell:

- `backend/config/urls.py` registers `path("app/", spa_entry)` before `include("dashboard.urls")`.
- `backend/config/urls.py` registers `path("coach/", spa_entry)` and `re_path(r"^coach/(?P<path>.*)$", spa_entry)` before `include("dashboard.urls")`.
- Because Django resolves URL patterns in order, legacy `dashboard.urls` entries for `app/` and `coach/plans/` are currently shadowed by the SPA routes.

This means the legacy rendered dashboard templates and static JS are no longer the normal runtime path for `/app/` or `/coach/*`, but they are not safe to delete yet. They still have direct test coverage, named URL references, post/action handlers, and reusable services that the Vue API layer still depends on.

## Keep For Now

- `backend/dashboard/services/month_cards*.py`
- `backend/dashboard/services/imports*.py`
- `backend/dashboard/services/tasks.py`
- `backend/dashboard/views_shared.py`
- `backend/dashboard/handlers/planned_training_api.py`
- `backend/dashboard/texts.py`
- `backend/templates/includes/_top_nav.html`
- `backend/templates/includes/_notifications_dropdown.html`

Reason: these provide business logic, import behavior, shared update helpers, auth redirects, or public/base shell pieces still used by API views or non-SPA pages.

## Remove After Route Switch Is Fully Settled

- `backend/templates/dashboard/dashboard.html`
- `backend/templates/dashboard/coach_training_plans.html`
- `backend/templates/dashboard/_assets.html`
- `backend/templates/dashboard/_month_cards.html`
- `backend/templates/dashboard/_planned_week_table.html`
- `backend/templates/dashboard/_completed_week_table.html`
- `backend/templates/dashboard/_month_switcher.html`
- `backend/templates/dashboard/_planned_km_rules_modal.html`
- `backend/templates/dashboard/_coach_sidebar.html`
- `backend/templates/dashboard/_coach_main_toolbar.html`
- `backend/templates/dashboard/_coach_manage_modal.html`
- `backend/templates/dashboard/_coach_remove_athlete_modal.html`
- `backend/templates/dashboard/_import_modal.html`
- `backend/templates/dashboard/_legend_modals.html`
- `backend/dashboard/static/js/dashboard.js`
- `backend/dashboard/static/js/dashboard_api.js`
- `backend/dashboard/static/js/dashboard_bootstrap.js`
- `backend/dashboard/static/js/dashboard_coach.js`
- `backend/dashboard/static/js/dashboard_core.js`
- `backend/dashboard/static/js/dashboard_editor_completed.js`
- `backend/dashboard/static/js/dashboard_editor_planned.js`
- `backend/dashboard/static/js/dashboard_fit_import.js`
- `backend/dashboard/static/js/dashboard_garmin.js`
- `backend/dashboard/static/js/dashboard_inline_shared.js`
- `backend/dashboard/static/js/dashboard_legend_shortcuts.js`
- `backend/dashboard/static/js/dashboard_metrics.js`
- `backend/dashboard/static/js/dashboard_month.js`
- `backend/dashboard/static/css/dashboard.css`
- `backend/dashboard/static/css/dashboard_coach.css`
- `backend/dashboard/static/css/dashboard_editor.css`
- `backend/dashboard/static/css/dashboard_import.css`
- `backend/dashboard/static/css/dashboard_legend.css`
- `backend/dashboard/static/css/dashboard_month.css`
- `backend/dashboard/static/css/dashboard_responsive.css`

Reason: these are legacy rendered dashboard UI assets. They are currently shadowed for `/app/` and `/coach/*`, but still covered by legacy regression tests and may still be valuable as a rollback reference until Vue reaches final rollout.

## Needs Manual QA Before Removal

- `backend/dashboard/views_home.py`
- `backend/dashboard/views_coach.py`
- `backend/dashboard/views_athlete_api.py`
- `backend/dashboard/handlers/home_actions.py`
- `backend/dashboard/handlers/coach_page_actions.py`
- `backend/dashboard/urls.py`
- `backend/dashboard/tests/test_dashboard_frontend_regressions.py`
- `backend/dashboard/tests/_fit_import_*`
- `backend/dashboard/tests/_coach_training_*`
- `backend/accounts/tests.py`
- `backend/dashboard/tests/test_profile_manage.py`

Reason: these files mix three concerns:

- old rendered page GET/POST behavior
- legacy JSON/action endpoints under paths such as `/plans/update/`
- business rules and regression expectations that have been partially reimplemented under `/api/v1/`

Before removal, update or replace tests that currently call `reverse("dashboard_home")` or `reverse("coach_training_plans")` expecting legacy rendered HTML. At runtime those URLs now resolve to SPA responses because of `backend/config/urls.py` ordering.

## Remove Now

None.

Reason: the route switch makes legacy UI a cleanup candidate, but not a zero-risk deletion candidate. The remaining named URL references and regression tests should be migrated deliberately.

## Recommended Next Step

Do a focused "route and test realignment" slice:

- Add/keep tests proving `/app/` and `/coach/*` render `spa.html`.
- Move remaining legacy endpoint coverage from `dashboard.tests` to `/api/v1/` coverage where the API already exists.
- Replace top-nav links that still reverse legacy names only if product wants canonical SPA route names instead of legacy-compatible names.
- After dashboard tests no longer assert legacy templates for runtime routes, delete legacy rendered UI files in one small removal PR/slice.
