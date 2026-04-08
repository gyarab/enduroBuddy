import { apiClient } from "@/api/client";
export async function connectGarmin(email, password) {
    const response = await apiClient.post("/imports/garmin/connect/", { email, password });
    return response.data;
}
export async function revokeGarmin() {
    const response = await apiClient.post("/imports/garmin/revoke/");
    return response.data;
}
export async function startGarminSync(range) {
    const response = await apiClient.post("/imports/garmin/start/", { range });
    return response.data;
}
export async function fetchImportJobStatus(jobId) {
    const response = await apiClient.get(`/imports/jobs/${jobId}/status/`);
    return response.data;
}
export async function uploadFitFile(file) {
    const body = new FormData();
    body.append("fit_file", file);
    const response = await apiClient.post("/imports/fit/", body, {
        headers: {
            "Content-Type": "multipart/form-data",
        },
    });
    return response.data;
}
