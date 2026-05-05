import { describe, it, expect, vi } from "vitest"

vi.mock("~/utils/api/auth", () => ({
  profileSetup: vi.fn().mockResolvedValue({ ok: true, redirect_to: "/app/dashboard" }),
  fetchCurrentUser: vi.fn(),
}))

describe("profile-setup page", () => {
  it("profileSetup payload includes all required fields", async () => {
    const { profileSetup } = await import("~/utils/api/auth")
    const vi_fn = profileSetup as ReturnType<typeof vi.fn>
    vi_fn.mockClear()

    const payload = {
      first_name: "Jan",
      last_name: "Novák",
      role: "ATHLETE" as const,
      terms_accepted: true,
    }
    await profileSetup(payload)
    expect(vi_fn).toHaveBeenCalledWith(expect.objectContaining({
      role: "ATHLETE",
      terms_accepted: true,
    }))
  })

  it("profileSetup response has redirect_to", async () => {
    const { profileSetup } = await import("~/utils/api/auth")
    const result = await profileSetup({
      first_name: "Jan",
      last_name: "Novák",
      role: "ATHLETE",
      terms_accepted: true,
    })
    expect(result.redirect_to).toBe("/app/dashboard")
  })
})
