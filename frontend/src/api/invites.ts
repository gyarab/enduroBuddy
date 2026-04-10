import { apiClient } from "@/api/client";

export type InviteDetail = {
  group_name: string;
  coach_name: string;
  is_expired: boolean;
  is_used: boolean;
};

export async function fetchInvite(token: string) {
  const response = await apiClient.get<{ ok: boolean } & InviteDetail>(`/invites/${token}/`);
  return response.data;
}

export async function acceptInvite(token: string) {
  const response = await apiClient.post<{ ok: boolean; message: string }>(`/invites/${token}/accept/`);
  return response.data;
}
