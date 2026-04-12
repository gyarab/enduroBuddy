import { apiClient } from "@/api/client";

export type ProfileCompletionPayload = {
  first_name: string;
  last_name: string;
  role: "COACH" | "ATHLETE";
  role_options: Array<{
    value: "COACH" | "ATHLETE";
    label: string;
  }>;
  google_profile_completed: boolean;
  google_role_confirmed: boolean;
  next: string;
};

export type ProfileCompletionSaveResponse = {
  ok: boolean;
  message: string;
  redirect_to: string;
  profile: {
    first_name: string;
    last_name: string;
    role: "COACH" | "ATHLETE";
    google_profile_completed: boolean;
    google_role_confirmed: boolean;
  };
};

export type ProfileSettingsPayload = {
  first_name: string;
  last_name: string;
  full_name: string;
  email: string;
  role: "COACH" | "ATHLETE";
  language: string;
  default_app_route: string;
  password_change_url: string;
  logout_url: string;
};

export async function fetchProfileCompletion(next?: string) {
  const response = await apiClient.get<ProfileCompletionPayload>("/profile/complete/", {
    params: next ? { next } : undefined,
  });
  return response.data;
}

export async function saveProfileCompletion(payload: {
  first_name: string;
  last_name: string;
  role: "COACH" | "ATHLETE";
  next?: string;
}) {
  const response = await apiClient.patch<ProfileCompletionSaveResponse>("/profile/complete/", payload);
  return response.data;
}

export async function fetchProfileSettings() {
  const response = await apiClient.get<{ ok: boolean; profile: ProfileSettingsPayload }>("/profile/settings/");
  return response.data.profile;
}

export async function saveProfileSettings(payload: {
  first_name: string;
  last_name: string;
}) {
  const response = await apiClient.patch<{ ok: boolean; message: string; profile: ProfileSettingsPayload }>("/profile/settings/", payload);
  return response.data;
}
