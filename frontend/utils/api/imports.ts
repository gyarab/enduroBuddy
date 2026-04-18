import { apiFetch } from "~/utils/apiFetch"

export type GarminConnectionState = {
  connected: boolean
  display_name: string
}

export type ImportJob = {
  id: number
  status: string
  status_label: string
  progress_percent: number
  window?: string
  message: string
  total_count?: number
  processed_count?: number
  imported_count?: number
  skipped_count?: number
  done: boolean
}

export async function connectGarmin(email: string, password: string) {
  return apiFetch<{
    ok: boolean
    message: string
    connection: GarminConnectionState
  }>("/imports/garmin/connect/", { method: "POST", body: { email, password } })
}

export async function revokeGarmin() {
  return apiFetch<{
    ok: boolean
    message: string
    connection: GarminConnectionState
  }>("/imports/garmin/revoke/", { method: "POST" })
}

export async function startGarminSync(range: string) {
  return apiFetch<{
    ok: boolean
    job: ImportJob
    already_running: boolean
    message: string
  }>("/imports/garmin/start/", { method: "POST", body: { range } })
}

export async function fetchImportJobStatus(jobId: number) {
  return apiFetch<{ ok: boolean; job: ImportJob }>(`/imports/jobs/${jobId}/status/`)
}

export async function uploadFitFile(file: File) {
  const body = new FormData()
  body.append("fit_file", file)
  return apiFetch<{
    ok: boolean
    queued?: boolean
    imported?: boolean
    message: string
  }>("/imports/fit/", { method: "POST", body })
}

export async function garminWeekSync(weekStart: string) {
  return apiFetch<{
    ok: boolean
    replaced: number
    untouched: number
    message: string
  }>("/imports/garmin/week-sync/", { method: "POST", body: { week_start: weekStart } })
}
