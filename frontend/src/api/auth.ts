import { apiClient } from "@/api/client";

export type AuthMeResponse = {
  id: number;
  full_name: string;
  email: string;
  role: "COACH" | "ATHLETE";
  initials: string;
  capabilities: {
    can_view_coach: boolean;
    can_view_athlete: boolean;
    can_complete_profile: boolean;
    has_garmin_connection: boolean;
    garmin_connect_enabled: boolean;
    garmin_sync_enabled: boolean;
    coached_athlete_count: number;
  };
  default_app_route: string;
};

export async function fetchCurrentUser() {
  const response = await apiClient.get<AuthMeResponse>("/auth/me/");
  return response.data;
}
