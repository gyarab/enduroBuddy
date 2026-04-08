import { apiClient } from "@/api/client";
export async function fetchCoachDashboard(athleteId, month) {
    const response = await apiClient.get("/coach/dashboard/", {
        params: {
            ...(athleteId ? { athlete_id: athleteId } : {}),
            ...(month ? { month } : {}),
        },
    });
    return response.data;
}
export async function fetchCoachAthletes(athleteId) {
    const response = await apiClient.get("/coach/athletes/", {
        params: athleteId ? { athlete_id: athleteId } : undefined,
    });
    return response.data;
}
export async function updateCoachAthleteFocus(athleteId, focus) {
    const response = await apiClient.patch("/coach/athlete-focus/", {
        athlete_id: athleteId,
        focus,
    });
    return response.data;
}
export async function reorderCoachAthletes(athleteIds) {
    const response = await apiClient.patch("/coach/reorder-athletes/", {
        athlete_ids: athleteIds,
    });
    return response.data;
}
export async function updateCoachAthleteVisibility(athleteId, hidden) {
    const response = await apiClient.patch("/coach/athlete-visibility/", {
        athlete_id: athleteId,
        hidden,
    });
    return response.data;
}
export async function updateCoachPlannedTraining(plannedId, payload) {
    const response = await apiClient.patch(`/coach/training/planned/${plannedId}/`, payload);
    return response.data;
}
export async function addCoachSecondPhaseTraining(plannedId) {
    const response = await apiClient.post(`/coach/training/planned/${plannedId}/second-phase/`);
    return response.data;
}
export async function removeCoachSecondPhaseTraining(plannedId) {
    const response = await apiClient.delete(`/coach/training/planned/${plannedId}/second-phase/`);
    return response.data;
}
