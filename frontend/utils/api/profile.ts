import { apiFetch } from "~/utils/apiFetch"

export type ProfileCompletionPayload = {
  first_name: string
  last_name: string
  role: "COACH" | "ATHLETE"
  role_options: Array<{
    value: "COACH" | "ATHLETE"
    label: string
  }>
  google_profile_completed: boolean
  google_role_confirmed: boolean
  next: string
}

export type ProfileCompletionSaveResponse = {
  ok: boolean
  message: string
  redirect_to: string
  profile: {
    first_name: string
    last_name: string
    role: "COACH" | "ATHLETE"
    google_profile_completed: boolean
    google_role_confirmed: boolean
  }
}

export type ProfileSettingsPayload = {
  first_name: string
  last_name: string
  full_name: string
  email: string
  role: "COACH" | "ATHLETE"
  language: string
  default_app_route: string
  password_change_url: string
  logout_url: string
}

export async function fetchProfileCompletion(next?: string) {
  return apiFetch<ProfileCompletionPayload>("/profile/complete/", {
    params: next ? { next } : undefined,
  })
}

export async function saveProfileCompletion(payload: {
  first_name: string
  last_name: string
  role: "COACH" | "ATHLETE"
  next?: string
}) {
  return apiFetch<ProfileCompletionSaveResponse>("/profile/complete/", {
    method: "PATCH",
    body: payload,
  })
}

export async function fetchProfileSettings() {
  const data = await apiFetch<{ ok: boolean; profile: ProfileSettingsPayload }>("/profile/settings/")
  return data.profile
}

export async function saveProfileSettings(payload: {
  first_name: string
  last_name: string
}) {
  return apiFetch<{ ok: boolean; message: string; profile: ProfileSettingsPayload }>(
    "/profile/settings/",
    { method: "PATCH", body: payload },
  )
}
