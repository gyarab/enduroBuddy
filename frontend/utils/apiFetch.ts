export interface ApiOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE"
  body?: Record<string, unknown> | FormData
  params?: Record<string, string | number | boolean>
}

function getCsrfToken(): string | null {
  if (import.meta.server) return null
  const match = document.cookie.match(/(?:^|; )endurobuddy_csrftoken=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : null
}

export async function apiFetch<T = unknown>(
  path: string,
  options: ApiOptions = {},
): Promise<T> {
  const csrfToken = getCsrfToken()

  return $fetch<T>(path.startsWith("/api/") ? path : `/api/v1${path}`, {
    credentials: "include",
    headers: {
      Accept: "application/json",
      "X-Requested-With": "XMLHttpRequest",
      ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
    },
    method: options.method ?? "GET",
    ...(options.body ? { body: options.body } : {}),
    ...(options.params ? { params: options.params } : {}),
  })
}
