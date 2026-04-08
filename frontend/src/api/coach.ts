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

export type CoachAthletesPayload = {
  athletes: CoachAthlete[];
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

export async function fetchCoachAthletes(athleteId?: number) {
  const response = await apiClient.get<CoachAthletesPayload>("/coach/athletes/", {
    params: athleteId ? { athlete_id: athleteId } : undefined,
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

export async function reorderCoachAthletes(athleteIds: number[]) {
  const response = await apiClient.patch<CoachAthletesPayload>("/coach/reorder-athletes/", {
    athlete_ids: athleteIds,
  });
  return response.data;
}

export async function updateCoachAthleteVisibility(athleteId: number, hidden: boolean) {
  const response = await apiClient.patch<CoachAthletesPayload & { ok: boolean; athlete_id: number; hidden: boolean }>(
    "/coach/athlete-visibility/",
    {
      athlete_id: athleteId,
      hidden,
    },
  );
  return response.data;
}

export async function updateCoachPlannedTraining(
  plannedId: number,
  payload: {
    field: "title" | "notes" | "session_type";
    value: string;
  },
) {
  const response = await apiClient.patch(`/coach/training/planned/${plannedId}/`, payload);
  return response.data;
}

export async function addCoachSecondPhaseTraining(plannedId: number) {
  const response = await apiClient.post(`/coach/training/planned/${plannedId}/second-phase/`);
  return response.data;
}

export async function removeCoachSecondPhaseTraining(plannedId: number) {
  const response = await apiClient.delete(`/coach/training/planned/${plannedId}/second-phase/`);
  return response.data;
}
