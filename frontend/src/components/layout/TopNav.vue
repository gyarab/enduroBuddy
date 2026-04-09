<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute } from "vue-router";

import NotificationBell from "@/components/layout/NotificationBell.vue";
import ProfileDropdown from "@/components/layout/ProfileDropdown.vue";
import { useI18n } from "@/composables/useI18n";
import { useAuthStore } from "@/stores/auth";
import { useCoachStore } from "@/stores/coach";
import { useTrainingStore } from "@/stores/training";

const props = defineProps<{
  variant: "athlete" | "coach";
}>();

const authStore = useAuthStore();
const coachStore = useCoachStore();
const trainingStore = useTrainingStore();
const route = useRoute();
const isProfileOpen = ref(false);
const brandLogoUrl = "/static/brand/eb-logo-compact.svg";
const { t } = useI18n();

const title = computed(() => {
  if (route.path.startsWith("/coach")) {
    return t("topNav.coachWorkspace");
  }
  if (route.path.includes("/profile")) {
    return t("topNav.completeProfile");
  }
  return t("topNav.dashboard");
});

const subtitle = computed(() => {
  if (props.variant === "coach") {
    if (coachStore.selectedAthlete?.name) {
      if (coachStore.selectedMonth?.label) {
        return `${coachStore.selectedAthlete.name} / ${coachStore.selectedMonth.label}`;
      }
      return coachStore.selectedAthlete.name;
    }
    return authStore.user?.capabilities.coached_athlete_count
      ? t("topNav.athletesReady", { count: authStore.user.capabilities.coached_athlete_count })
      : t("topNav.plansAndFocus");
  }
  return trainingStore.selectedMonth?.label || t("topNav.dashboardOverview");
});
</script>

<template>
  <header class="top-nav">
    <div class="top-nav__inner">
      <a class="top-nav__brand" :href="props.variant === 'coach' ? '/coach/plans' : '/app/dashboard'">
        <img :src="brandLogoUrl" alt="EnduroBuddy" />
      </a>

      <div class="top-nav__headline">
        <div class="top-nav__title">{{ title }}</div>
        <div class="top-nav__subtitle">{{ subtitle }}</div>
      </div>

      <div class="top-nav__actions">
        <NotificationBell />

        <div class="top-nav__profile">
          <button class="top-nav__avatar" type="button" @click="isProfileOpen = !isProfileOpen">
            {{ authStore.user?.initials || "EB" }}
          </button>
          <ProfileDropdown v-if="isProfileOpen" />
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  height: var(--eb-topnav-height);
  border-bottom: 1px solid var(--eb-border);
  background: var(--eb-bg-elevated);
  backdrop-filter: blur(12px);
}

.top-nav__inner {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: var(--eb-spacing-4);
  max-width: calc(var(--eb-shell-max-width) + 3rem);
  height: 100%;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.top-nav__brand img {
  height: 1.75rem;
}

.top-nav__headline {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  min-width: 0;
}

.top-nav__title {
  font-family: var(--eb-font-display);
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.top-nav__subtitle {
  color: var(--eb-text-muted);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.top-nav__actions {
  display: flex;
  align-items: center;
  gap: var(--eb-spacing-3);
}

.top-nav__profile {
  position: relative;
}

.top-nav__avatar {
  display: inline-grid;
  place-items: center;
  width: 2.25rem;
  height: 2.25rem;
  border: 1px solid var(--eb-border);
  border-radius: 999px;
  background: var(--eb-surface);
  color: var(--eb-text);
  font-size: 0.8125rem;
  font-weight: 600;
}

.top-nav__avatar:hover {
  border-color: rgba(200, 255, 0, 0.3);
  box-shadow: var(--eb-glow-lime);
}

@media (max-width: 767px) {
  .top-nav__inner {
    padding: 0 1rem;
    gap: 0.75rem;
  }

  .top-nav__subtitle {
    display: none;
  }
}
</style>
