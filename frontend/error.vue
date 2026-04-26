<template>
  <div class="eb-error-root">
    <div class="eb-error-card">
      <div class="eb-error-code">{{ error.statusCode }}</div>
      <h1 class="eb-error-title">{{ title }}</h1>
      <p class="eb-error-message">{{ error.message }}</p>
      <NuxtLink to="/" class="eb-btn eb-btn-primary">
        {{ t("error.goHome") }}
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { NuxtError } from "#app"

const props = defineProps<{ error: NuxtError }>()
const { t } = useI18n()

const title = computed(() => {
  if (props.error.statusCode === 404) return t("error.notFound")
  if (props.error.statusCode === 403) return t("error.forbidden")
  return t("error.generic")
})
</script>

<style scoped>
.eb-error-root {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--eb-bg);
}
.eb-error-card {
  text-align: center;
  padding: 3rem;
}
.eb-error-code {
  font-family: var(--eb-font-mono);
  font-size: 6rem;
  color: var(--eb-lime);
  line-height: 1;
}
.eb-error-title {
  font-family: var(--eb-font-display);
  font-size: 2rem;
  color: var(--eb-text);
  margin: 1rem 0 0.5rem;
}
.eb-error-message {
  color: var(--eb-text-muted);
  margin-bottom: 2rem;
}
.eb-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  border-radius: var(--eb-radius-md);
  font-family: var(--eb-font-body);
  font-size: 0.875rem;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  border: none;
  transition: opacity 0.15s;
}
.eb-btn-primary {
  background: var(--eb-lime);
  color: var(--eb-bg);
}
.eb-btn-primary:hover {
  opacity: 0.9;
}
</style>
