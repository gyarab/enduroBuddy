import { apiClient } from "@/api/client";
export async function fetchCurrentUser() {
    const response = await apiClient.get("/auth/me/");
    return response.data;
}
