import { vi } from "vitest"

// Stub Nuxt auto-imported globals for unit tests
vi.stubGlobal("useI18n", () => ({ t: (k: string) => k }))
vi.stubGlobal("useCookie", () => ({ value: null }))
vi.stubGlobal("$fetch", vi.fn())
vi.stubGlobal("useNuxtApp", () => ({
  $i18n: { t: (k: string) => k },
}))
