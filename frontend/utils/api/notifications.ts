import { apiFetch } from "~/utils/apiFetch"

export type AppNotification = {
  id: number
  kind: string
  tone: "success" | "info" | "warning" | "danger" | "secondary"
  text: string
  actor: string
  created_at: string | null
  read_at: string | null
  unread: boolean
}

export type NotificationsResponse = {
  ok: boolean
  notifications: AppNotification[]
  unread_count: number
}

export async function fetchNotifications() {
  return apiFetch<NotificationsResponse>("/notifications/")
}

export async function markNotificationsRead(notificationIds: number[]) {
  return apiFetch<{ ok: boolean; marked_count: number }>("/notifications/mark-read/", {
    method: "POST",
    body: { notification_ids: notificationIds },
  })
}
