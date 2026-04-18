import { apiFetch } from "~/utils/apiFetch"

export type InviteDetail = {
  group_name: string
  coach_name: string
  is_expired: boolean
  is_used: boolean
}

export async function fetchInvite(token: string): Promise<InviteDetail> {
  const data = await apiFetch<{ ok: boolean } & InviteDetail>(`/invites/${token}/`)
  const { ok: _ok, ...invite } = data
  return invite as InviteDetail
}

export async function acceptInvite(token: string) {
  return apiFetch<{ ok: boolean; message: string }>(`/invites/${token}/accept/`, { method: "POST" })
}
