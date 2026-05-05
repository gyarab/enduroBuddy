<template>
  <AuthFlowView :auth-screen="screen" />
</template>

<script setup lang="ts">
definePageMeta({ layout: "auth" })

const route = useRoute()

const slug = computed(() => {
  const parts = route.params.slug as string[]
  const filtered = Array.isArray(parts) ? parts.filter(Boolean) : [String(parts)].filter(Boolean)
  return filtered.join("/")
})

const screenMap: Record<string, string> = {
  "login": "login",
  "signup": "signup",
  "logout": "logout",
  "password/reset": "password-reset",
  "password/reset/done": "password-reset-done",
  "confirm-email": "verification-sent",
  "inactive": "inactive",
  "email": "email-management",
  "password/change": "password-change",
  "password/set": "password-set",
  "password/reset/key/done": "password-reset-key-done",
  "social/login/error": "social-error",
  "social/login/cancelled": "social-cancelled",
  "social/connections": "connections",
  "reauthenticate": "reauthenticate",
}

const screen = computed(() => {
  const path = slug.value
  if (path.startsWith("confirm-email/") && path.length > "confirm-email/".length) {
    return "email-confirm-key"
  }
  // password/reset/key/<uidb36>-<key>/ pattern
  if (path.startsWith("password/reset/key/") && path !== "password/reset/key/done") {
    return "password-reset-key"
  }
  return screenMap[path] ?? "login"
})
</script>
