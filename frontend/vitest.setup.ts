import { vi } from "vitest"
import en from "./i18n/locales/cs.json"

function resolveKey(obj: Record<string, unknown>, key: string): string | null {
  const val = key.split(".").reduce((acc: unknown, part: string) => {
    if (acc && typeof acc === "object") return (acc as Record<string, unknown>)[part]
    return null
  }, obj)
  return typeof val === "string" ? val : null
}

function interpolate(template: string, params: Record<string, unknown> = {}): string {
  return template.replace(/\{(\w+)\}/g, (_, k) => String(params[k] ?? `{${k}}`))
}

function t(key: string, params?: Record<string, unknown>): string {
  const translation = resolveKey(en as Record<string, unknown>, key)
  if (!translation) return key
  return params ? interpolate(translation, params) : translation
}

// Stub Nuxt auto-imported globals for unit tests
vi.stubGlobal("useI18n", () => ({ t, locale: { value: "en" } }))
vi.stubGlobal("useCookie", () => ({ value: null }))
vi.stubGlobal("$fetch", vi.fn())
vi.stubGlobal("useNuxtApp", () => ({
  $i18n: { t },
}))
vi.stubGlobal("navigateTo", vi.fn())
vi.stubGlobal("defineNuxtRouteMiddleware", (fn: Function) => fn)
vi.stubGlobal("useRuntimeConfig", () => ({ public: { appHost: "" } }))
