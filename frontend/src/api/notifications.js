import { apiClient } from "@/api/client";
export async function fetchNotifications() {
    const response = await apiClient.get("/notifications/");
    return response.data;
}
export async function markNotificationsRead(notificationIds) {
    const response = await apiClient.post("/notifications/mark-read/", {
        notification_ids: notificationIds,
    });
    return response.data;
}
