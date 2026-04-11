# SPA Polish Audit

Date: 2026-04-11

## Scope

This audit closes the main "partially done" frontend items that remained after the Vue migration:

- profile/settings surface in SPA
- route/test realignment evidence for SPA runtime ownership
- visual/mobile follow-up for shell-level interactions
- documentation refresh against real repo state

## Result

Status: mostly closed

The authenticated app no longer depends on the old profile modal as its primary profile surface. Vue now owns:

- profile settings entry from the top nav dropdown
- editable first name / last name account surface
- language toggle inside SPA settings
- clear links to password change and logout flows

Legacy cleanup is now clearly a cleanup phase, not a missing-feature phase. Tests now explicitly prove that:

- `/app/dashboard` renders `spa.html`
- `/coach/plans` renders `spa.html`

## Visual / Mobile Notes

Shipped in this pass:

- top nav now handles profile dropdown close-on-outside-click
- top nav mobile layout wraps month navigation onto its own row
- profile settings modal uses stacked mobile layout
- settings actions remain reachable on smaller screens without relying on hidden legacy UI

Still worth a final manual QA pass:

- coach sidebar open/close feel on narrow screens
- long athlete names in coach top nav
- imports modal density on smaller mobile heights
- inline editor comfort for heavy editing sessions on phone

## Documentation Alignment

Refreshed in this pass:

- `2026-04-08-vue-frontend-implementation-plan.md`
- `2026-04-09-vue-frontend-continuation-plan.md`
- `2026-04-09-legacy-dashboard-cleanup-audit.md`

Main correction:

- the repo is beyond "migration in progress" for the core frontend
- the remaining work is now profile polish closure, final QA, and deliberate legacy removal
