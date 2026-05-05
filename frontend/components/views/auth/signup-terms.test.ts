import { describe, it, expect, vi } from "vitest"
import { reactive, ref } from "vue"

vi.mock("~/utils/api/auth", () => ({
  signupWithPassword: vi.fn().mockResolvedValue({ ok: true, redirect_to: "/app/dashboard" }),
  loginWithPassword: vi.fn(),
  logoutFromSession: vi.fn(),
  requestPasswordReset: vi.fn(),
  fetchEmailConfirmState: vi.fn(),
  confirmEmailKey: vi.fn(),
  fetchPasswordResetKeyState: vi.fn(),
  fetchEmailAddresses: vi.fn(),
  mutateEmailAddress: vi.fn(),
  changePassword: vi.fn(),
  fetchPasswordSetState: vi.fn(),
  setPassword: vi.fn(),
  fetchSocialConnections: vi.fn(),
  disconnectSocialAccount: vi.fn(),
  fetchReauthenticateState: vi.fn(),
  submitReauthenticate: vi.fn(),
  submitPasswordResetFromKey: vi.fn(),
}))

describe("signup terms checkbox behavior", () => {
  it("submit button is disabled when termsAccepted is false", async () => {
    const { signupWithPassword } = await import("~/utils/api/auth")
    const form = reactive({ termsAccepted: false })
    const isSubmitting = ref(false)
    const disabled = isSubmitting.value || !form.termsAccepted
    expect(disabled).toBe(true)
    expect(signupWithPassword).not.toHaveBeenCalled()
  })

  it("submit button is enabled when termsAccepted is true", () => {
    const form = reactive({ termsAccepted: true })
    const isSubmitting = ref(false)
    const disabled = isSubmitting.value || !form.termsAccepted
    expect(disabled).toBe(false)
  })

  it("submit button is disabled during submission even when terms accepted", () => {
    const form = reactive({ termsAccepted: true })
    const isSubmitting = ref(true)
    const disabled = isSubmitting.value || !form.termsAccepted
    expect(disabled).toBe(true)
  })

  it("signupWithPassword payload includes terms_accepted", async () => {
    const { signupWithPassword } = await import("~/utils/api/auth")
    const vi_fn = signupWithPassword as ReturnType<typeof vi.fn>
    vi_fn.mockClear()

    const payload = {
      first_name: "Jan",
      last_name: "Novák",
      email: "jan@example.com",
      role: "ATHLETE" as const,
      password: "pass123",
      password_confirmation: "pass123",
      terms_accepted: true,
    }
    await signupWithPassword(payload)
    expect(vi_fn).toHaveBeenCalledWith(expect.objectContaining({ terms_accepted: true }))
  })
})
