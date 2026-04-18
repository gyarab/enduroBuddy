import { apiFetch } from "~/utils/apiFetch"

export type TrainingRow = {
  id: number | null
  kind: "planned" | "completed"
  status: "planned" | "done" | "missed" | "rest"
  date: string | null
  day_label: string
  title: string
  notes: string
  session_type: "RUN" | "WORKOUT"
  planned_metrics: {
    planned_km_value: number
    planned_km_text: string
    planned_km_confidence: "high" | "medium" | "low"
    planned_km_show: boolean
    planned_km_line_km: string
    planned_km_line_reason: string
    planned_km_line_where: string
  } | null
  completed_metrics: {
    km: string
    minutes: string
    details: string
    avg_hr: number | null
    max_hr: number | null
  } | null
  editable: boolean
  is_second_phase?: boolean
  can_add_second_phase?: boolean
  can_remove_second_phase?: boolean
  has_linked_activity?: boolean
}

export type DashboardWeek = {
  id: number
  week_index: number
  week_start: string
  week_end: string
  has_started: boolean
  planned_total_km_text: string
  completed_total: {
    km: string
    time: string
    avg_hr: number | null
    max_hr: number | null
  }
  planned_rows: TrainingRow[]
  completed_rows: TrainingRow[]
}

export type DashboardPayload = {
  selected_month: {
    id: number
    value: string
    label: string
    year: number
    month: number
  } | null
  navigation: {
    previous: { value: string; label: string } | null
    next: { value: string; label: string } | null
    available: Array<{ id: number; value: string; label: string }>
  }
  summary: {
    planned_sessions: number
    completed_sessions: number
    planned_km: number
    completed_km: number
    completed_minutes: number
    completion_rate: number
  }
  weeks: DashboardWeek[]
  flags: {
    is_coach: boolean
    can_edit_planned: boolean
    can_edit_completed: boolean
  }
}

export type PlannedTrainingDraft = {
  date: string
  title?: string
  notes?: string
  session_type?: "RUN" | "WORKOUT"
}

export async function fetchDashboard(month?: string) {
  return apiFetch<DashboardPayload>("/dashboard/", {
    params: month ? { month } : undefined,
  })
}

export async function createPlannedTraining(payload: PlannedTrainingDraft) {
  return apiFetch("/training/planned/", { method: "POST", body: payload })
}

export async function updatePlannedTraining(
  plannedId: number,
  payload: {
    field: "title" | "notes" | "session_type"
    value: string
  },
) {
  return apiFetch(`/training/planned/${plannedId}/`, { method: "PATCH", body: payload })
}

export async function deletePlannedTraining(plannedId: number) {
  return apiFetch(`/training/planned/${plannedId}/`, { method: "DELETE" })
}

export async function updateCompletedTraining(
  plannedId: number,
  payload: {
    field: "km" | "min" | "third" | "avg_hr" | "max_hr"
    value: string
  },
) {
  return apiFetch(`/training/completed/${plannedId}/`, { method: "PATCH", body: payload })
}

export async function addSecondPhaseTraining(plannedId: number) {
  return apiFetch(`/training/planned/${plannedId}/second-phase/`, { method: "POST" })
}

export async function removeSecondPhaseTraining(plannedId: number) {
  return apiFetch(`/training/planned/${plannedId}/second-phase/`, { method: "DELETE" })
}

export async function addNextMonth(athleteId?: number) {
  return apiFetch<{
    ok: boolean
    month_created: boolean
    weeks_created: number
    days_created: number
    month_value: string
  }>("/training/months/", {
    method: "POST",
    body: athleteId ? { athlete_id: athleteId } : {},
  })
}
