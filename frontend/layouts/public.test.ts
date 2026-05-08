import { mount } from "@vue/test-utils"
import { createPinia, setActivePinia } from "pinia"
import { RouterLink, createRouter, createMemoryHistory } from "vue-router"
import { beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/components/ui/EbLogo.vue", () => ({ default: { template: "<span />" } }))

const mockInitialize = vi.fn()
const mockAuth = {
  hasBootstrapped: true,
  isAuthenticated: false,
  initialize: mockInitialize,
}

vi.mock("~/stores/auth", () => ({
  useAuthStore: vi.fn(() => mockAuth),
}))

import PublicLayout from "@/layouts/public.vue"

function makeRouter() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", component: { template: "<div/>" } },
      { path: "/dashboard", component: { template: "<div/>" } },
      { path: "/accounts/login/", component: { template: "<div/>" } },
    ],
  })
  router.push("/")
  return router
}

describe("public layout header", () => {
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    vi.clearAllMocks()
    mockAuth.isAuthenticated = false
    mockAuth.hasBootstrapped = true
  })

  it("shows login link when unauthenticated", async () => {
    const router = makeRouter()
    await router.isReady()
    const wrapper = mount(PublicLayout, {
      global: { plugins: [router, pinia], stubs: { NuxtLink: RouterLink } },
    })
    expect(wrapper.find('a[href="/accounts/login/"]').exists()).toBe(true)
    expect(wrapper.find('a[href="/dashboard"]').exists()).toBe(false)
  })

  it("shows dashboard link when authenticated", async () => {
    mockAuth.isAuthenticated = true
    const router = makeRouter()
    await router.isReady()
    const wrapper = mount(PublicLayout, {
      global: { plugins: [router, pinia], stubs: { NuxtLink: RouterLink } },
    })
    expect(wrapper.find('a[href="/dashboard"]').exists()).toBe(true)
    expect(wrapper.find('a[href="/accounts/login/"]').exists()).toBe(false)
  })

  it("calls initialize() on mount when not yet bootstrapped", async () => {
    mockAuth.hasBootstrapped = false
    const router = makeRouter()
    await router.isReady()
    mount(PublicLayout, {
      global: { plugins: [router, pinia], stubs: { NuxtLink: RouterLink } },
    })
    expect(mockInitialize).toHaveBeenCalledOnce()
  })
})
