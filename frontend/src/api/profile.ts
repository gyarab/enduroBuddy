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
