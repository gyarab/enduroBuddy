import { beforeEach, describe, expect, it, vi } from "vitest"

const mockInitialize = vi.fn()
let mockIsAuthenticated = true
let mockHasBootstrapped = true
let mockAppHost = ""

vi.mock("~/stores/auth", () => ({
  useAuthStore: vi.fn(() => ({
    hasBootstrapped: mockHasBootstrapped,
    isAuthenticated: mockIsAuthenticated,
    initialize: mockInitialize,
  })),
}))

vi.stubGlobal("useRuntimeConfig", () => ({ public: { appHost: mockAppHost } }))

import authMiddleware from "./auth.global"

const mockNavigateTo = vi.mocked(navigateTo)

function route(path: string) {
  return { path } as Parameters<typeof authMiddleware>[0]
}

describe("auth.global middleware", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockIsAuthenticated = true
    mockHasBootstrapped = true
    mockAppHost = ""
  })

  it("does nothing for public path /about", async () => {
    await authMiddleware(route("/about"), {} as any)
    expect(mockNavigateTo).not.toHaveBeenCalled()
  })

  it("does nothing for public path /", async () => {
    await authMiddleware(route("/"), {} as any)
    expect(mockNavigateTo).not.toHaveBeenCalled()
  })

  it("does nothing for authenticated user on /dashboard", async () => {
    await authMiddleware(route("/dashboard"), {} as any)
    expect(mockNavigateTo).not.toHaveBeenCalled()
  })

  it("does nothing for authenticated user on /app/settings", async () => {
    await authMiddleware(route("/app/settings"), {} as any)
    expect(mockNavigateTo).not.toHaveBeenCalled()
  })

  it("redirects to /accounts/login/ when unauthenticated on /dashboard (no appHost)", async () => {
    mockIsAuthenticated = false
    await authMiddleware(route("/dashboard"), {} as any)
    expect(mockNavigateTo).toHaveBeenCalledWith("/accounts/login/")
  })

  it("redirects to /accounts/login/ when unauthenticated on /app/dashboard (no appHost)", async () => {
    mockIsAuthenticated = false
    await authMiddleware(route("/app/dashboard"), {} as any)
    expect(mockNavigateTo).toHaveBeenCalledWith("/accounts/login/")
  })

  it("redirects to /accounts/login/ when unauthenticated on /coach/plans (no appHost)", async () => {
    mockIsAuthenticated = false
    await authMiddleware(route("/coach/plans"), {} as any)
    expect(mockNavigateTo).toHaveBeenCalledWith("/accounts/login/")
  })

  it("redirects to public domain login when unauthenticated and appHost is set", async () => {
    mockIsAuthenticated = false
    mockAppHost = "app.endurobuddy.cz"
    await authMiddleware(route("/dashboard"), {} as any)
    expect(mockNavigateTo).toHaveBeenCalledWith(
      "https://endurobuddy.cz/accounts/login/",
      { external: true },
    )
  })

  it("calls initialize() when not yet bootstrapped", async () => {
    mockHasBootstrapped = false
    mockIsAuthenticated = false
    await authMiddleware(route("/dashboard"), {} as any)
    expect(mockInitialize).toHaveBeenCalledOnce()
  })
})
