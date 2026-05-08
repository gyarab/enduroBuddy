# Spec: Public layout auth-aware header

**Date:** 2026-05-08  
**Branch:** `feat/public-auth-header`  
**Status:** Approved

---

## Problem

The public landing page (`endurobuddy.cz/`) currently auto-redirects authenticated users away to `app.endurobuddy.cz/dashboard`. This is disruptive — a logged-in user cannot browse the public site. Additionally, the public layout always shows "Login →" regardless of auth state, which is confusing for users who are already signed in.

---

## Goal

- Authenticated users can stay on `endurobuddy.cz` and browse public pages normally.
- The public layout header shows **"Dashboard →"** when the user is logged in, and **"Login →"** when not.
- "Dashboard →" links to `/dashboard` (resolved to `app.endurobuddy.cz/dashboard` in production via existing `domains.global.ts` cross-domain routing).
- After logout, user lands on `/accounts/login/` (existing backend behavior, unchanged).
- `/dashboard`, `/app/*`, `/coach/*` remain protected — unauthenticated access is blocked by `auth.global.ts` (unchanged).

---

## What changes

### 1. `frontend/middleware/domains.global.ts`

Remove the block that auto-redirects authenticated users from public pages to the app domain (currently lines 28–39):

```ts
// REMOVE THIS ENTIRE BLOCK:
if (import.meta.client) {
  const auth = useAuthStore()
  if (!auth.hasBootstrapped) {
    await auth.initialize()
  }
  const PUBLIC_PAGES = ["/", "/about", "/terms", "/privacy"]
  if (isPublicDomain && PUBLIC_PAGES.includes(to.path) && auth.isAuthenticated) {
    const target = auth.isCoach ? "/coach/plans" : "/dashboard"
    return navigateTo(`https://${appHost}${target}`, { external: true })
  }
}
```

The two remaining rules stay unchanged:
- `app domain + public path` → redirect to public domain
- `public domain + app path` → redirect to app domain

### 2. `frontend/layouts/public.vue`

Add auth check after hydration. In `<script setup>`:

```ts
const auth = useAuthStore()
onMounted(async () => {
  if (!auth.hasBootstrapped) await auth.initialize()
})
```

Replace the static login button in the template:

```html
<!-- before -->
<NuxtLink to="/accounts/login/" class="eb-btn-nav">
  {{ t("nav.login") }} →
</NuxtLink>

<!-- after -->
<NuxtLink v-if="auth.isAuthenticated" to="/dashboard" class="eb-btn-nav">
  {{ t("nav.dashboard") }} →
</NuxtLink>
<NuxtLink v-else to="/accounts/login/" class="eb-btn-nav">
  {{ t("nav.login") }} →
</NuxtLink>
```

### 3. I18n keys

Add `nav.dashboard` to both locale files:

- `frontend/i18n/locales/cs.json`: `"dashboard": "Dashboard"`
- `frontend/i18n/locales/en.json`: `"dashboard": "Dashboard"`

---

## What does NOT change

| Component | Why |
|---|---|
| `auth.global.ts` | Protected paths `/dashboard`, `/app/*`, `/coach/*` already block unauthenticated access |
| Backend logout | Returns `redirect_to: "/accounts/login/"` — correct |
| `domains.global.ts` cross-domain rules | App path on public domain → app domain; public path on app domain → public domain |
| All other middleware | Unchanged |

---

## User journeys

### Unauthenticated user visits `endurobuddy.cz/`
1. Landing page renders (SSR) with "Login →" button
2. After hydration: `auth.initialize()` → 401 → `isAuthenticated = false` → button stays "Login →"
3. User clicks login → `/accounts/login/`

### Authenticated user visits `endurobuddy.cz/`
1. Landing page renders (SSR) with "Login →" (before hydration)
2. After hydration: `auth.initialize()` → 200 → `isAuthenticated = true` → button switches to "Dashboard →"
3. User clicks "Dashboard →" → navigates to `/dashboard`
4. In production: `domains.global.ts` catches `/dashboard` on public domain → redirects to `https://app.endurobuddy.cz/dashboard`
5. `auth.global.ts` on app domain: authenticated → allows access

### After logout
1. Frontend POSTs to `/api/v1/auth/logout/`
2. Backend returns `redirect_to: "/accounts/login/"`
3. Frontend hard-redirects to `/accounts/login/`
4. Next visit to landing page: `auth.initialize()` → 401 → "Login →"

---

## UX trade-off: SSR flash

The "Login →" button renders server-side (before JS hydration). Authenticated users will briefly see "Login →" before it switches to "Dashboard →". This is acceptable — consistent with the existing pattern where auth checks in this app are all client-side only (`auth.global.ts` has `if (import.meta.server) return`). The flash lasts less than one second on a typical connection.

---

## Tests

Add / extend tests for `public.vue` layout:
- Unauthenticated: renders "Login →" link pointing to `/accounts/login/`
- Authenticated: renders "Dashboard →" link pointing to `/dashboard`

---

## Branch cleanup

Before starting implementation, delete merged branches:
- `feat/registration-flow` — merged, KOMPLETNÍ per CLAUDE.md
- Any other merged branches visible in `git branch -r`

New branch: `feat/public-auth-header`
