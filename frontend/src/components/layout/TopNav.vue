<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import LegendModal from "@/components/layout/LegendModal.vue";
import NotificationBell from "@/components/layout/NotificationBell.vue";
import ProfileDropdown from "@/components/layout/ProfileDropdown.vue";
import ProfileSettingsModal from "@/components/layout/ProfileSettingsModal.vue";
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
const isProfileSettingsOpen = ref(false);
const isLegendOpen = ref(false);
const profileRootRef = ref<HTMLElement | null>(null);
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

const activeMonth = computed(() => {
  return props.variant === "coach" ? coachStore.selectedMonth : trainingStore.selectedMonth;
});

const activeNavigation = computed(() => {
  return props.variant === "coach" ? coachStore.navigation : trainingStore.navigation;
});

const activeAthleteName = computed(() => {
  return props.variant === "coach" ? coachStore.selectedAthlete?.name || "" : "";
});

const showMonthNavigator = computed(() => Boolean(activeMonth.value?.label));

async function goToPreviousMonth() {
  if (!activeNavigation.value?.previous || authStore.isLoading) {
    return;
  }
  if (props.variant === "coach") {
    await coachStore.goToPreviousMonth();
    return;
  }
  await trainingStore.goToPreviousMonth();
}

async function goToNextMonth() {
  if (!activeNavigation.value?.next || authStore.isLoading) {
    return;
  }
  if (props.variant === "coach") {
    await coachStore.goToNextMonth();
    return;
  }
  await trainingStore.goToNextMonth();
}

function handleDocumentClick(event: MouseEvent) {
  const target = event.target;
  if (!(target instanceof Node)) {
    return;
  }
  if (profileRootRef.value && !profileRootRef.value.contains(target)) {
    isProfileOpen.value = false;
  }
}

function openProfileSettings() {
  isProfileOpen.value = false;
  isProfileSettingsOpen.value = true;
}

onMounted(() => {
  document.addEventListener("click", handleDocumentClick);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", handleDocumentClick);
});
</script>

<template>
  <header class="top-nav">
    <div class="top-nav__inner">
      <a class="top-nav__brand" :href="props.variant === 'coach' ? '/coach/plans' : '/app/dashboard'">
        <img :src="brandLogoUrl" alt="EnduroBuddy" />
      </a>

      <div v-if="showMonthNavigator" class="top-nav__month-nav" aria-label="Month navigation">
        <span v-if="activeAthleteName" class="top-nav__athlete-pill">{{ activeAthleteName }}</span>
        <button
          class="top-nav__month-button"
          type="button"
          :disabled="!activeNavigation?.previous"
          :aria-label="activeNavigation?.previous?.label || 'Previous month'"
          @click="goToPreviousMonth"
        >
          &lt;
        </button>
        <div class="top-nav__month-label">{{ activeMonth?.label }}</div>
        <button
          class="top-nav__month-button"
          type="button"
          :disabled="!activeNavigation?.next"
          :aria-label="activeNavigation?.next?.label || 'Next month'"
          @click="goToNextMonth"
        >
          &gt;
        </button>
      </div>

      <div v-else class="top-nav__headline">
        <div class="top-nav__title">{{ title }}</div>
        <div class="top-nav__subtitle">{{ subtitle }}</div>
      </div>

      <div class="top-nav__actions">
        <button class="top-nav__legend-btn" type="button" @click="isLegendOpen = true">
          {{ t("legend.button") }}
        </button>
        <NotificationBell />

        <div ref="profileRootRef" class="top-nav__profile">
          <button class="top-nav__avatar" type="button" @click.stop="isProfileOpen = !isProfileOpen">
            {{ authStore.user?.initials || "EB" }}
          </button>
          <ProfileDropdown v-if="isProfileOpen" @open-settings="openProfileSettings" />
        </div>
      </div>
    </div>
  </header>

  <LegendModal :open="isLegendOpen" @close="isLegendOpen = false" />
  <ProfileSettingsModal :open="isProfileSettingsOpen" @close="isProfileSettingsOpen = false" />
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

.top-nav__month-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.65rem;
  min-width: 0;
}

.top-nav__athlete-pill {
  display: inline-flex;
  align-items: center;
  min-height: 1.75rem;
  max-width: 14rem;
  padding: 0 0.75rem;
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: 999px;
  background: rgba(56, 189, 248, 0.12);
  color: var(--eb-blue);
  font-size: var(--eb-type-label-size);
  font-weight: 700;
  letter-spacing: var(--eb-type-label-tracking);
  overflow: hidden;
  text-overflow: ellipsis;
  text-transform: uppercase;
  white-space: nowrap;
}

.top-nav__month-button {
  display: inline-grid;
  place-items: center;
  width: 1.75rem;
  height: 1.75rem;
  border: 0;
  border-radius: var(--eb-radius-sm);
  background: transparent;
  color: var(--eb-text-soft);
  font-family: var(--eb-font-mono);
  font-size: var(--eb-type-mono-size);
  transition:
    background-color 150ms ease-out,
    color 150ms ease-out;
}

.top-nav__month-button:not(:disabled):hover {
  background: var(--eb-surface-hover);
  color: var(--eb-text);
}

.top-nav__month-button:disabled {
  cursor: not-allowed;
  opacity: 0.35;
}

.top-nav__month-label {
  min-width: 8.75rem;
  color: var(--eb-text);
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-h3-size);
  font-weight: 600;
  letter-spacing: var(--eb-type-h3-tracking);
  text-align: center;
}

.top-nav__title {
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-h3-size);
  font-weight: 700;
  letter-spacing: var(--eb-type-h3-tracking);
}

.top-nav__subtitle {
  color: var(--eb-text-muted);
  font-size: var(--eb-type-label-size);
  text-transform: uppercase;
  letter-spacing: var(--eb-type-label-tracking);
}

.top-nav__actions {
  display: flex;
  align-items: center;
  gap: var(--eb-spacing-3);
}

.top-nav__legend-btn {
  padding: 0.35rem 0.85rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-sm);
  background: transparent;
  color: var(--eb-text-soft);
  font-size: var(--eb-type-small-size);
  font-weight: 600;
  letter-spacing: var(--eb-type-small-tracking);
  text-transform: uppercase;
  cursor: pointer;
  transition:
    border-color 150ms ease-out,
    color 150ms ease-out;
}

.top-nav__legend-btn:hover {
  border-color: rgba(200, 255, 0, 0.3);
  color: var(--eb-lime);
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
  font-size: var(--eb-type-small-size);
  font-weight: 600;
}

.top-nav__avatar:hover {
  border-color: rgba(200, 255, 0, 0.3);
  box-shadow: var(--eb-glow-lime);
}

@media (max-width: 767px) {
  .top-nav {
    height: auto;
    min-height: var(--eb-topnav-height);
  }

  .top-nav__inner {
    grid-template-columns: auto minmax(0, 1fr);
    padding: 0.7rem 1rem;
    gap: 0.6rem;
  }

  .top-nav__subtitle {
    display: none;
  }

  .top-nav__brand img {
    height: 1.5rem;
  }

  .top-nav__month-nav {
    grid-column: 1 / -1;
    order: 3;
    gap: 0.4rem;
    justify-content: flex-start;
    flex-wrap: wrap;
  }

  .top-nav__athlete-pill {
    display: none;
  }

  .top-nav__month-label {
    min-width: 0;
    max-width: 7.5rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .top-nav__actions {
    justify-self: end;
  }
}
</style>
