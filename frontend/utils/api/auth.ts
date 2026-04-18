import { apiFetch } from "~/utils/apiFetch"

export type AuthMeResponse = {
  id: number
  full_name: string
  email: string
  role: "COACH" | "ATHLETE"
  initials: string
  capabilities: {
    can_view_coach: boolean
    can_view_athlete: boolean
    can_complete_profile: boolean
    has_garmin_connection: boolean
    garmin_connect_enabled: boolean
    garmin_sync_enabled: boolean
    coached_athlete_count: number
  }
  default_app_route: string
}

export async function fetchCurrentUser() {
  return apiFetch<AuthMeResponse>("/auth/me/")
}

export type LoginPayload = {
  email: string
  password: string
  remember: boolean
}

export type SignupPayload = {
  first_name: string
  last_name: string
  email: string
  role: "COACH" | "ATHLETE"
  password: string
  password_confirmation: string
}

export type AuthActionResponse = {
  ok: boolean
  message: string
  redirect_to: string
  errors?: Record<string, string[]>
}

export async function loginWithPassword(payload: LoginPayload) {
  return apiFetch<AuthActionResponse>("/auth/login/", { method: "POST", body: payload })
}

export async function signupWithPassword(payload: SignupPayload) {
  return apiFetch<AuthActionResponse>("/auth/signup/", { method: "POST", body: payload })
}

export async function requestPasswordReset(email: string) {
  return apiFetch<AuthActionResponse>("/auth/password/reset/", { method: "POST", body: { email } })
}

export async function logoutFromSession() {
  return apiFetch<AuthActionResponse>("/auth/logout/", { method: "POST" })
}

export type EmailConfirmState = {
  ok: boolean
  can_confirm: boolean
  email?: string
  user?: {
    display: string
  }
  message?: string
}

export type PasswordResetKeyState = {
  ok: boolean
  token_valid: boolean
  message?: string
  redirect_to?: string
}

export type EmailAddressItem = {
  email: string
  verified: boolean
  primary: boolean
  can_delete: boolean
  can_mark_primary: boolean
}

export type EmailAddressesState = {
  ok: boolean
  emails: EmailAddressItem[]
  can_add_email: boolean
  current_email: string
}

export type PasswordSetState = {
  ok: boolean
  has_usable_password: boolean
  redirect_to: string
}

export type SocialConnectionItem = {
  id: number
  provider: string
  provider_name: string
  brand_name: string
  label: string
  uid: string
}

export type SocialConnectionsState = {
  ok: boolean
  accounts: SocialConnectionItem[]
  connect_google_url: string
}

export type ReauthenticateState = {
  ok: boolean
  next: string
  has_usable_password: boolean
}

export async function fetchEmailConfirmState(key: string) {
  return apiFetch<EmailConfirmState>(`/auth/email/confirm/${key}/`)
}

export async function confirmEmailKey(key: string) {
  return apiFetch<AuthActionResponse>(`/auth/email/confirm/${key}/`, { method: "POST" })
}

export async function fetchPasswordResetKeyState(uidb36: string, key: string) {
  return apiFetch<PasswordResetKeyState>(`/auth/password/reset/key/${uidb36}-${key}/`)
}

export async function submitPasswordResetFromKey(
  uidb36: string,
  key: string,
  password: string,
  passwordConfirmation: string,
) {
  return apiFetch<AuthActionResponse>(`/auth/password/reset/key/${uidb36}-${key}/`, {
    method: "POST",
    body: { password, password_confirmation: passwordConfirmation },
  })
}

export async function fetchEmailAddresses() {
  return apiFetch<EmailAddressesState>("/auth/email/")
}

export async function mutateEmailAddress(
  action: "add" | "primary" | "send" | "remove",
  payload: { email?: string; new_email?: string },
) {
  return apiFetch<AuthActionResponse & { emails?: EmailAddressItem[] }>("/auth/email/", {
    method: "POST",
    body: { action, ...payload },
  })
}

export async function changePassword(
  currentPassword: string,
  password: string,
  passwordConfirmation: string,
) {
  return apiFetch<AuthActionResponse>("/auth/password/change/", {
    method: "POST",
    body: {
      current_password: currentPassword,
      password,
      password_confirmation: passwordConfirmation,
    },
  })
}

export async function fetchPasswordSetState() {
  return apiFetch<PasswordSetState>("/auth/password/set/")
}

export async function setPassword(password: string, passwordConfirmation: string) {
  return apiFetch<AuthActionResponse>("/auth/password/set/", {
    method: "POST",
    body: { password, password_confirmation: passwordConfirmation },
  })
}

export async function fetchSocialConnections() {
  return apiFetch<SocialConnectionsState>("/auth/social/connections/")
}

export async function disconnectSocialAccount(accountId: number) {
  return apiFetch<AuthActionResponse & { accounts?: SocialConnectionItem[] }>(
    "/auth/social/connections/",
    { method: "POST", body: { account_id: accountId } },
  )
}

export async function fetchReauthenticateState(next?: string) {
  return apiFetch<ReauthenticateState>("/auth/reauthenticate/", {
    params: next ? { next } : undefined,
  })
}

export async function submitReauthenticate(password: string, next?: string) {
  return apiFetch<AuthActionResponse>("/auth/reauthenticate/", {
    method: "POST",
    body: { password, next },
  })
}
