import { apiClient } from "@/api/client";

export type AppNotification = {
  id: number;
  kind: string;
  tone: "success" | "info" | "warning" | "danger" | "secondary";
  text: string;
  actor: string;
  created_at: string | null;
  read_at: string | null;
  unread: boolean;
};

export type NotificationsResponse = {
  ok: boolean;
  notifications: AppNotification[];
  unread_count: number;
};

export async function fetchNotifications() {
  const response = await apiClient.get<NotificationsResponse>("/notifications/");
  return response.data;
}

export async function markNotificationsRead(notificationIds: number[]) {
  const response = await apiClient.post<{ ok: boolean; marked_count: number }>("/notifications/mark-read/", {
    notification_ids: notificationIds,
  });
  return response.data;
}
