import { apiFetch } from "~/utils/apiFetch"
import type { DashboardPayload, PlannedTrainingDraft } from "~/utils/api/training"

export type CoachAthlete = {
  id: number
  name: string
  focus: string
  hidden: boolean
  sort_order: number
  selected: boolean
}

export type CoachAthletesPayload = {
  athletes: CoachAthlete[]
}

export type CoachDashboardPayload = DashboardPayload & {
  selected_athlete: {
    id: number
    name: string
    focus: string
  } | null
  athletes: CoachAthlete[]
}

export async function fetchCoachDashboard(athleteId?: number, month?: string) {
  return apiFetch<CoachDashboardPayload>("/coach/dashboard/", {
    params: {
      ...(athleteId ? { athlete_id: athleteId } : {}),
      ...(month ? { month } : {}),
    },
  })
}

export async function fetchCoachAthletes(athleteId?: number) {
  return apiFetch<CoachAthletesPayload>("/coach/athletes/", {
    params: athleteId ? { athlete_id: athleteId } : undefined,
  })
}

export async function updateCoachAthleteFocus(athleteId: number, focus: string) {
  return apiFetch<{ ok: boolean; athlete_id: number; focus: string }>("/coach/athlete-focus/", {
    method: "PATCH",
    body: { athlete_id: athleteId, focus },
  })
}

export async function reorderCoachAthletes(athleteIds: number[]) {
  return apiFetch<CoachAthletesPayload>("/coach/reorder-athletes/", {
    method: "PATCH",
    body: { athlete_ids: athleteIds },
  })
}

export async function updateCoachAthleteVisibility(athleteId: number, hidden: boolean) {
  return apiFetch<CoachAthletesPayload & { ok: boolean; athlete_id: number; hidden: boolean }>(
    "/coach/athlete-visibility/",
    { method: "PATCH", body: { athlete_id: athleteId, hidden } },
  )
}

export async function updateCoachPlannedTraining(
  plannedId: number,
  payload: {
    field: "title" | "notes" | "session_type"
    value: string
  },
) {
  return apiFetch(`/coach/training/planned/${plannedId}/`, { method: "PATCH", body: payload })
}

export async function createCoachPlannedTraining(athleteId: number, payload: PlannedTrainingDraft) {
  return apiFetch("/coach/training/planned/", {
    method: "POST",
    body: { ...payload, athlete_id: athleteId },
  })
}

export async function deleteCoachPlannedTraining(plannedId: number) {
  return apiFetch(`/coach/training/planned/${plannedId}/`, { method: "DELETE" })
}

export async function addCoachSecondPhaseTraining(plannedId: number) {
  return apiFetch(`/coach/training/planned/${plannedId}/second-phase/`, { method: "POST" })
}

export async function removeCoachSecondPhaseTraining(plannedId: number) {
  return apiFetch(`/coach/training/planned/${plannedId}/second-phase/`, { method: "DELETE" })
}

export type CoachJoinRequest = {
  id: number
  athlete_name: string
  athlete_username: string
  created_at: string
}

export async function fetchCoachCode() {
  return apiFetch<{ ok: boolean; coach_join_code: string }>("/coach/code/")
}

export async function fetchJoinRequests() {
  return apiFetch<{ ok: boolean; requests: CoachJoinRequest[] }>("/coach/join-requests/")
}

export async function approveJoinRequest(requestId: number) {
  return apiFetch<{ ok: boolean; request_id: number }>(
    `/coach/join-requests/${requestId}/approve/`,
    { method: "POST" },
  )
}

export async function rejectJoinRequest(requestId: number) {
  return apiFetch<{ ok: boolean; request_id: number }>(
    `/coach/join-requests/${requestId}/reject/`,
    { method: "POST" },
  )
}

export async function requestCoachByCode(coachCode: string) {
  return apiFetch<{ ok: boolean; coach_name: string }>("/coach/join-request/", {
    method: "POST",
    body: { coach_code: coachCode },
  })
}

export async function removeAthlete(athleteId: number, confirmName: string) {
  return apiFetch<{ ok: boolean; removed_athlete_id: number }>(`/coach/athletes/${athleteId}/`, {
    method: "DELETE",
    body: { confirm_name: confirmName },
  })
}
