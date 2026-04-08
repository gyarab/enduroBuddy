import { apiClient } from "@/api/client";

export type GarminConnectionState = {
  connected: boolean;
  display_name: string;
};

export type ImportJob = {
  id: number;
  status: string;
  status_label: string;
  progress_percent: number;
  window?: string;
  message: string;
  total_count?: number;
  processed_count?: number;
  imported_count?: number;
  skipped_count?: number;
  done: boolean;
};

export async function connectGarmin(email: string, password: string) {
  const response = await apiClient.post<{
    ok: boolean;
    message: string;
    connection: GarminConnectionState;
  }>("/imports/garmin/connect/", { email, password });
  return response.data;
}

export async function revokeGarmin() {
  const response = await apiClient.post<{
    ok: boolean;
    message: string;
    connection: GarminConnectionState;
  }>("/imports/garmin/revoke/");
  return response.data;
}

export async function startGarminSync(range: string) {
  const response = await apiClient.post<{
    ok: boolean;
    job: ImportJob;
    already_running: boolean;
    message: string;
  }>("/imports/garmin/start/", { range });
  return response.data;
}

export async function fetchImportJobStatus(jobId: number) {
  const response = await apiClient.get<{ ok: boolean; job: ImportJob }>(`/imports/jobs/${jobId}/status/`);
  return response.data;
}

export async function uploadFitFile(file: File) {
  const body = new FormData();
  body.append("fit_file", file);
  const response = await apiClient.post<{
    ok: boolean;
    queued?: boolean;
    imported?: boolean;
    message: string;
  }>("/imports/fit/", body, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
}
