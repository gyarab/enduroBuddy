<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import GarminImportModal from "@/components/training/GarminImportModal.vue";
import ProfileDropdown from "@/components/layout/ProfileDropdown.vue";
import ProfileSettingsModal from "@/components/layout/ProfileSettingsModal.vue";
import { useAuthStore } from "@/stores/auth";
import { useCoachStore } from "@/stores/coach";
import { useLegendStore } from "@/stores/legend";
import { useTrainingStore } from "@/stores/training";

const props = defineProps<{
  variant: "athlete" | "coach";
}>();

const authStore = useAuthStore();
const coachStore = useCoachStore();
const legendStore = useLegendStore();
const trainingStore = useTrainingStore();
const { t } = useI18n();

const isProfileOpen = ref(false);
const isProfileSettingsOpen = ref(false);
const isGarminOpen = ref(false);
const profileRootRef = ref<HTMLElement | null>(null);

const monthLabel = computed(() => {
  if (props.variant === "coach") return coachStore.selectedMonth?.label ?? "";
  return trainingStore.selectedMonth?.label ?? "";
});

const showSync = computed(() => props.variant === "athlete" && !!authStore.user?.capabilities?.garmin_connect_enabled);
const showCoachBtn = computed(() => authStore.isCoach && props.variant === "athlete");
const showLegendBtn = computed(() => props.variant === "athlete");
const showMyPlanBtn = computed(() => props.variant === "coach");

const username = computed(() => {
  const u = authStore.user;
  if (!u) return "";
  return `${u.first_name ?? ""} ${u.last_name ?? ""}`.trim();
});

function handleDocumentClick(event: MouseEvent) {
  const target = event.target;
  if (!(target instanceof Node)) return;
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

onMounted(() => document.addEventListener("click", handleDocumentClick));
onBeforeUnmount(() => document.removeEventListener("click", handleDocumentClick));
</script>

<template>
  <header class="top-nav">
    <!-- Left: logo + username -->
    <div class="nav-left">
      <RouterLink class="nav-brand" :to="variant === 'coach' ? '/coach/plans' : '/app/dashboard'">
        <span class="nav-brand__mark" aria-hidden="true">
          <span /><span /><span />
        </span>
        <span class="nav-brand__text">
          <span class="nav-brand__name">EnduroBuddy</span>
          <span class="nav-brand__username">{{ username }}</span>
        </span>
      </RouterLink>
    </div>

    <!-- Center: month -->
    <div class="nav-center">
      <div class="nav-month">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" class="nav-month__icon">
          <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/>
          <line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
        </svg>
        {{ monthLabel }}
      </div>
    </div>

    <!-- Right: action buttons -->
    <div class="nav-right">
      <!-- Coach btn (athlete view, isCoach) -->
      <RouterLink v-if="showCoachBtn" class="nav-btn nav-btn--coach" to="/coach/plans" :title="t('topNav.switchToCoach')">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M8 3 4 7l4 4"/><path d="M4 7h16"/><path d="M16 21l4-4-4-4"/><path d="M20 17H4"/>
        </svg>
        {{ t("topNav.switchToCoach") }}
      </RouterLink>
      <div v-if="showCoachBtn && showSync" class="nav-divider" aria-hidden="true" />

      <!-- Můj plán btn (coach view) — BEFORE sync -->
      <RouterLink v-if="showMyPlanBtn" class="nav-btn nav-btn--myplan" to="/dashboard" :title="t('topNav.myPlan')">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M8 3 4 7l4 4"/><path d="M4 7h16"/><path d="M16 21l4-4-4-4"/><path d="M20 17H4"/>
        </svg>
        {{ t("topNav.myPlan") }}
      </RouterLink>
      <div v-if="showMyPlanBtn && showSync" class="nav-divider" aria-hidden="true" />

      <!-- Sync btn (Garmin enabled) -->
      <button v-if="showSync" class="nav-btn nav-btn--sync" type="button" :title="t('imports.open')" @click="isGarminOpen = true">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
          <path d="M21 3v5h-5"/>
          <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
          <path d="M3 21v-5h5"/>
        </svg>
      </button>
      <div v-if="showLegendBtn && showSync" class="nav-divider" aria-hidden="true" />

      <!-- Legend btn (athlete view only) -->
      <button v-if="showLegendBtn" class="nav-btn nav-btn--legend" type="button" :title="t('legend.button')" @click="legendStore.isPanelOpen = true">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
          <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
        </svg>
      </button>

      <!-- Avatar -->
      <div v-if="authStore.isAuthenticated" ref="profileRootRef" class="nav-profile">
        <button class="nav-avatar" type="button" @click.stop="isProfileOpen = !isProfileOpen">
          {{ authStore.user?.initials || "?" }}
        </button>
        <ProfileDropdown v-if="isProfileOpen" @open-settings="openProfileSettings" />
      </div>
    </div>
  </header>

  <ProfileSettingsModal :open="isProfileSettingsOpen" @close="isProfileSettingsOpen = false" />
  <GarminImportModal v-if="showSync" :open="isGarminOpen" @close="isGarminOpen = false" />
</template>

<style scoped>
.top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  height: 52px;
  background: var(--eb-bg-elevated, #18181b);
  border-bottom: 1px solid var(--eb-border);
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 1rem;
  padding: 0 20px;
  backdrop-filter: blur(12px);
}

/* Left */
.nav-left {
  display: flex;
  align-items: center;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
}

.nav-brand__mark {
  display: inline-flex;
  align-items: flex-end;
  gap: 0.2rem;
  height: 22px;
  transform: skewX(-6deg);
  flex-shrink: 0;
}

.nav-brand__mark span {
  width: 5px;
  border-radius: 2px;
  background: var(--eb-lime, #c8ff00);
  box-shadow: 0 0 8px rgba(200, 255, 0, 0.2);
}

.nav-brand__mark span:nth-child(1) { height: 38%; opacity: 0.35; }
.nav-brand__mark span:nth-child(2) { height: 65%; opacity: 0.65; }
.nav-brand__mark span:nth-child(3) { height: 100%; }

.nav-brand__text {
  display: flex;
  flex-direction: column;
  gap: 1px;
  line-height: 1;
}

.nav-brand__name {
  font-family: 'Syne', var(--eb-font-display, sans-serif);
  font-weight: 700;
  font-size: 15px;
  color: var(--eb-text, #fafafa);
  letter-spacing: -0.3px;
}

.nav-brand__username {
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 400;
  font-size: 10.5px;
  color: var(--eb-text-muted, #71717a);
}

/* Center */
.nav-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-month {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--eb-font-display, 'Outfit', sans-serif);
  font-weight: 600;
  font-size: 14px;
  color: #e4e4e7;
  white-space: nowrap;
}

.nav-month__icon {
  color: #52525b;
}

/* Right */
.nav-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 7px;
}

.nav-divider {
  width: 1px;
  height: 20px;
  background: #2e2e34;
  flex-shrink: 0;
}

/* Icon-only nav button */
.nav-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  border: 1px solid #3f3f46;
  border-radius: 7px;
  background: transparent;
  color: #71717a;
  cursor: pointer;
  flex-shrink: 0;
  text-decoration: none;
  transition: border-color 150ms ease-out, color 150ms ease-out;
  padding: 0;
  width: 32px;
}

.nav-btn:hover {
  border-color: #52525b;
  color: #a1a1aa;
}

/* Sync — green tint */
.nav-btn--sync {
  border-color: #2d5a2d;
  color: #7ecf7e;
  background: rgba(126, 207, 126, 0.06);
}

.nav-btn--sync:hover {
  border-color: #3a6e3a;
  color: #9ade9a;
}

/* Coach badge — lime, has text */
.nav-btn--coach {
  width: auto;
  padding: 0 11px;
  gap: 6px;
  border-color: #4d5e1a;
  background: rgba(200, 255, 0, 0.07);
  color: var(--eb-lime, #c8ff00);
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 700;
  font-size: 12px;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.nav-btn--coach:hover {
  border-color: rgba(200, 255, 0, 0.4);
  background: rgba(200, 255, 0, 0.12);
}

/* Můj plán — blue, has text */
.nav-btn--myplan {
  width: auto;
  padding: 0 11px;
  gap: 6px;
  border-color: rgba(56, 189, 248, 0.3);
  background: rgba(56, 189, 248, 0.07);
  color: var(--eb-blue, #38bdf8);
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 700;
  font-size: 12px;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.nav-btn--myplan:hover {
  border-color: rgba(56, 189, 248, 0.5);
  background: rgba(56, 189, 248, 0.12);
}

/* Avatar */
.nav-profile {
  position: relative;
}

.nav-avatar {
  display: inline-grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: 1px solid #3f3f46;
  border-radius: 50%;
  background: #27272a;
  color: var(--eb-lime, #c8ff00);
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 700;
  font-size: 10px;
  cursor: pointer;
  flex-shrink: 0;
  transition: border-color 150ms ease-out;
}

.nav-avatar:hover {
  border-color: rgba(200, 255, 0, 0.3);
}

@media (max-width: 767px) {
  .top-nav {
    padding: 0 12px;
    gap: 0.5rem;
  }

  .nav-brand__text {
    display: none;
  }

  .nav-month {
    font-size: 13px;
  }
}
</style>
