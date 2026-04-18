export interface ApiOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE"
  body?: Record<string, unknown> | FormData
  params?: Record<string, string | number | boolean>
}

export async function apiFetch<T = unknown>(
  path: string,
  options: ApiOptions = {},
): Promise<T> {
  const csrfToken = useCookie("endurobuddy_csrftoken")

  return $fetch<T>(path.startsWith("/api/") ? path : `/api/v1${path}`, {
    credentials: "include",
    headers: {
      Accept: "application/json",
      "X-Requested-With": "XMLHttpRequest",
      ...(csrfToken.value ? { "X-CSRFToken": csrfToken.value } : {}),
    },
    method: options.method ?? "GET",
    ...(options.body ? { body: options.body } : {}),
    ...(options.params ? { params: options.params } : {}),
  })
}
