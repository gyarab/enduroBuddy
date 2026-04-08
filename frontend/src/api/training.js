import { apiClient } from "@/api/client";
export async function fetchDashboard(month) {
    const response = await apiClient.get("/dashboard/", {
        params: month ? { month } : undefined,
    });
    return response.data;
}
export async function updatePlannedTraining(plannedId, payload) {
    const response = await apiClient.patch(`/training/planned/${plannedId}/`, payload);
    return response.data;
}
export async function updateCompletedTraining(plannedId, payload) {
    const response = await apiClient.patch(`/training/completed/${plannedId}/`, payload);
    return response.data;
}
export async function addSecondPhaseTraining(plannedId) {
    const response = await apiClient.post(`/training/planned/${plannedId}/second-phase/`);
    return response.data;
}
export async function removeSecondPhaseTraining(plannedId) {
    const response = await apiClient.delete(`/training/planned/${plannedId}/second-phase/`);
    return response.data;
}
