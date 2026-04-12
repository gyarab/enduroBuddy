<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import GarminImportModal from "@/components/training/GarminImportModal.vue";
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
const isGarminOpen = ref(false);
const profileRootRef = ref<HTMLElement | null>(null);
const logoFullUrl = "/static/brand/eb-logo-full.svg";
const logoMarkUrl = "/static/brand/eb-mark.svg";
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

function openGarmin() {
  isProfileOpen.value = false;
  isGarminOpen.value = true;
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
        <img class="top-nav__logo-full" :src="logoFullUrl" alt="EnduroBuddy" />
        <img class="top-nav__logo-mark" :src="logoMarkUrl" alt="EB" />
      </a>

      <div class="top-nav__headline">
        <div class="top-nav__title">{{ title }}</div>
        <div class="top-nav__subtitle">{{ subtitle }}</div>
      </div>

      <div class="top-nav__actions">
        <a
          v-if="authStore.isCoach && props.variant === 'athlete'"
          class="top-nav__coach-btn"
          href="/coach/plans"
        >
          {{ t("topNav.switchToCoach") }}
        </a>
        <button class="top-nav__legend-btn" type="button" @click="isLegendOpen = true">
          {{ t("legend.button") }}
        </button>
        <NotificationBell />

        <div ref="profileRootRef" class="top-nav__profile">
          <button class="top-nav__avatar" type="button" @click.stop="isProfileOpen = !isProfileOpen">
            {{ authStore.user?.initials || "EB" }}
          </button>
          <ProfileDropdown v-if="isProfileOpen" @open-settings="openProfileSettings" @open-garmin="openGarmin" />
        </div>
      </div>
    </div>
  </header>

  <LegendModal :open="isLegendOpen" @close="isLegendOpen = false" />
  <ProfileSettingsModal :open="isProfileSettingsOpen" @close="isProfileSettingsOpen = false" />
  <GarminImportModal :open="isGarminOpen" @close="isGarminOpen = false" />
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

.top-nav__logo-full {
  height: 1.75rem;
}

.top-nav__logo-mark {
  display: none;
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

.top-nav__coach-btn {
  display: inline-flex;
  align-items: center;
  padding: 0.35rem 0.85rem;
  border: 1px solid rgba(200, 255, 0, 0.3);
  border-radius: var(--eb-radius-sm);
  background: rgba(200, 255, 0, 0.08);
  color: var(--eb-lime);
  font-size: var(--eb-type-small-size);
  font-weight: 600;
  letter-spacing: var(--eb-type-small-tracking);
  text-transform: uppercase;
  transition:
    border-color 150ms ease-out,
    background-color 150ms ease-out;
}

.top-nav__coach-btn:hover {
  border-color: rgba(200, 255, 0, 0.5);
  background: rgba(200, 255, 0, 0.14);
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

  .top-nav__logo-full {
    display: none;
  }

  .top-nav__logo-mark {
    display: block;
    height: 1.5rem;
  }

  .top-nav__actions {
    justify-self: end;
  }
}
</style>
