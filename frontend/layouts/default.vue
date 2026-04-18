<template>
  <AppShell :variant="variant">
    <slot />
  </AppShell>
</template>

<script setup lang="ts">
import AppShell from "@/components/layout/AppShell.vue"
import { useRoute } from "vue-router"

const route = useRoute()

const variant = computed<"athlete" | "coach">(() => {
  return route.path.startsWith("/coach") ? "coach" : "athlete"
})
</script>
