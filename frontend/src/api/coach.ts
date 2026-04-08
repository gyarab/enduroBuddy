import { apiClient } from "@/api/client";
import type { DashboardPayload } from "@/api/training";

export type CoachAthlete = {
  id: number;
  name: string;
  focus: string;
  hidden: boolean;
  sort_order: number;
  selected: boolean;
};

export type CoachDashboardPayload = DashboardPayload & {
  selected_athlete: {
    id: number;
    name: string;
    focus: string;
  } | null;
  athletes: CoachAthlete[];
};

export async function fetchCoachDashboard(athleteId?: number, month?: string) {
  const response = await apiClient.get<CoachDashboardPayload>("/coach/dashboard/", {
    params: {
      ...(athleteId ? { athlete_id: athleteId } : {}),
      ...(month ? { month } : {}),
    },
  });
  return response.data;
}

export async function updateCoachAthleteFocus(athleteId: number, focus: string) {
  const response = await apiClient.patch<{ ok: boolean; athlete_id: number; focus: string }>("/coach/athlete-focus/", {
    athlete_id: athleteId,
    focus,
  });
  return response.data;
}
