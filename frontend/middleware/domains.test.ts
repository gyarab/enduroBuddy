import { beforeEach, describe, expect, it, vi } from "vitest"

const mockInitialize = vi.fn()
let mockIsAuthenticated = false
let mockIsCoach = false
let mockHasBootstrapped = true
let mockAppHost = "app.endurobuddy.cz"

vi.mock("~/stores/auth", () => ({
  useAuthStore: vi.fn(() => ({
    hasBootstrapped: mockHasBootstrapped,
    isAuthenticated: mockIsAuthenticated,
    isCoach: mockIsCoach,
    initialize: mockInitialize,
  })),
}))

vi.stubGlobal("useRuntimeConfig", () => ({ public: { appHost: mockAppHost } }))
vi.stubGlobal("useRequestHeaders", () => ({ host: "endurobuddy.cz" }))

import domainsMiddleware from "./domains.global"

const mockNavigateTo = vi.mocked(navigateTo)

function setHostname(hostname: string) {
  Object.defineProperty(window, "location", {
    value: { hostname },
    configurable: true,
    writable: true,
  })
}

function route(path: string) {
  return { path, fullPath: path } as Parameters<typeof domainsMiddleware>[0]
}

describe("domains.global middleware", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockIsAuthenticated = false
    mockIsCoach = false
    mockHasBootstrapped = true
    mockAppHost = "app.endurobuddy.cz"
    vi.stubGlobal("useRuntimeConfig", () => ({ public: { appHost: mockAppHost } }))
    setHostname("endurobuddy.cz")
  })

  it("returns early when appHost is not set", async () => {
    mockAppHost = ""
    vi.stubGlobal("useRuntimeConfig", () => ({ public: { appHost: "" } }))
    await domainsMiddleware(route("/"), {} as any)
    expect(mockNavigateTo).not.toHaveBeenCalled()
  })

  it("redirects public domain + app path to app domain", async () => {
    setHostname("endurobuddy.cz")
    await domainsMiddleware(route("/dashboard"), {} as any)
    expect(mockNavigateTo).toHaveBeenCalledWith(
      "https://app.endurobuddy.cz/dashboard",
      { external: true },
    )
  })

  it("redirects app domain + public path to public domain", async () => {
    setHostname("app.endurobuddy.cz")
    await domainsMiddleware(route("/"), {} as any)
    expect(mockNavigateTo).toHaveBeenCalledWith(
      "https://endurobuddy.cz/",
      { external: true },
    )
  })

  it("does NOT redirect authenticated user from public domain landing page", async () => {
    mockIsAuthenticated = true
    setHostname("endurobuddy.cz")
    await domainsMiddleware(route("/"), {} as any)
    expect(mockNavigateTo).not.toHaveBeenCalled()
  })

  it("does NOT redirect unauthenticated user from public domain about page", async () => {
    mockIsAuthenticated = false
    setHostname("endurobuddy.cz")
    await domainsMiddleware(route("/about"), {} as any)
    expect(mockNavigateTo).not.toHaveBeenCalled()
  })
})
