<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { changePassword } from "~/utils/api/auth";
import { requestCoachByCode } from "~/utils/api/coach";
import { fetchProfileSettings, saveProfileSettings, type ProfileSettingsPayload } from "~/utils/api/profile";
import EbModal from "@/components/ui/EbModal.vue";
import { useAuthStore } from "@/stores/auth";
import { useToastStore } from "@/stores/toasts";

const props = defineProps<{
  open: boolean;
}>();

const emit = defineEmits<{
  close: [];
}>();

const authStore = useAuthStore();
const toastStore = useToastStore();
const { t, locale, setLocale } = useI18n();

const profile = ref<ProfileSettingsPayload | null>(null);
const firstName = ref("");
const lastName = ref("");
const isLoading = ref(false);
const isSaving = ref(false);
const errorMessage = ref("");

const currentPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");
const isChangingPassword = ref(false);

const coachCode = ref("");
const isRequestingCoach = ref(false);

type Section = "profile" | "security" | "coach";
const activeSection = ref<Section>("profile");

const roleLabel = computed(() => {
  if (profile.value?.role === "COACH") return t("profileSettings.roleCoach");
  return t("profileSettings.roleAthlete");
});

const canChangePassword = computed(
  () => !!(currentPassword.value && newPassword.value && confirmPassword.value),
);

const showCoachSection = computed(() => profile.value?.role === "ATHLETE");

watch(
  () => props.open,
  async (open) => {
    if (!open) {
      errorMessage.value = "";
      activeSection.value = "profile";
      return;
    }
    isLoading.value = true;
    errorMessage.value = "";
    try {
      const nextProfile = await fetchProfileSettings();
      profile.value = nextProfile;
      firstName.value = nextProfile.first_name;
      lastName.value = nextProfile.last_name;
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : t("profileSettings.loadError");
    } finally {
      isLoading.value = false;
    }
  },
);

async function save() {
  isSaving.value = true;
  errorMessage.value = "";
  try {
    const response = await saveProfileSettings({
      first_name: firstName.value,
      last_name: lastName.value,
    });
    profile.value = response.profile;
    firstName.value = response.profile.first_name;
    lastName.value = response.profile.last_name;
    await authStore.refresh();
    toastStore.push(response.message, "success");
    emit("close");
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t("profileSettings.saveError");
    toastStore.push(errorMessage.value, "danger");
  } finally {
    isSaving.value = false;
  }
}

async function toggleLanguage() {
  await setLocale(locale.value === "cs" ? "en" : "cs");
  if (profile.value) profile.value = { ...profile.value, language: locale.value };
}

async function handleChangePassword() {
  if (!canChangePassword.value) return;
  isChangingPassword.value = true;
  try {
    await changePassword(currentPassword.value, newPassword.value, confirmPassword.value);
    toastStore.push(t("profileSettings.changePasswordSuccess"), "success");
    currentPassword.value = "";
    newPassword.value = "";
    confirmPassword.value = "";
  } catch (error) {
    toastStore.push(
      error instanceof Error ? error.message : t("profileSettings.changePasswordError"),
      "danger",
    );
  } finally {
    isChangingPassword.value = false;
  }
}

async function handleRequestCoach() {
  if (!coachCode.value.trim()) return;
  isRequestingCoach.value = true;
  try {
    const data = await requestCoachByCode(coachCode.value.trim());
    toastStore.push(t("profileSettings.requestCoachSuccess", { name: data.coach_name }), "success");
    coachCode.value = "";
  } catch {
    toastStore.push(t("profileSettings.requestCoachError"), "danger");
  } finally {
    isRequestingCoach.value = false;
  }
}
</script>

<template>
  <EbModal :open="open">
    <div class="ps">

      <!-- Header -->
      <div class="ps__header">
        <div class="ps__avatar">{{ authStore.user?.initials || "?" }}</div>
        <div class="ps__header-info">
          <div class="ps__display-name">
            {{ `${firstName} ${lastName}`.trim() || authStore.user?.email || "—" }}
          </div>
          <div class="ps__role-badge">{{ profile ? roleLabel : "…" }}</div>
        </div>
        <button class="ps__close" type="button" :aria-label="t('profileSettings.close')" @click="emit('close')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <!-- Loading / error (no sidebar yet) -->
      <div v-if="isLoading" class="ps__state">{{ t("profileSettings.loading") }}</div>
      <div v-else-if="errorMessage" class="ps__state ps__state--error">{{ errorMessage }}</div>

      <!-- Two-column body -->
      <div v-else-if="profile" class="ps__layout">

        <!-- Left nav -->
        <nav class="ps__nav">
          <button
            class="ps__nav-item"
            :class="{ 'ps__nav-item--active': activeSection === 'profile' }"
            type="button"
            @click="activeSection = 'profile'"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
            </svg>
            {{ t("profileSettings.identity") }}
          </button>
          <button
            class="ps__nav-item"
            :class="{ 'ps__nav-item--active': activeSection === 'security' }"
            type="button"
            @click="activeSection = 'security'"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            {{ t("profileSettings.security") }}
          </button>
          <button
            v-if="showCoachSection"
            class="ps__nav-item"
            :class="{ 'ps__nav-item--active': activeSection === 'coach' }"
            type="button"
            @click="activeSection = 'coach'"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            {{ t("profileSettings.connectCoach") }}
          </button>
        </nav>

        <!-- Right content -->
        <div class="ps__content">

          <!-- Profile section -->
          <section v-if="activeSection === 'profile'" class="ps__section">
            <div class="ps__section-label">{{ t("profileSettings.identity") }}</div>
            <label class="ps__field">
              <span>{{ t("profileSettings.firstName") }}</span>
              <input v-model="firstName" :disabled="isSaving" />
            </label>
            <label class="ps__field">
              <span>{{ t("profileSettings.lastName") }}</span>
              <input v-model="lastName" :disabled="isSaving" />
            </label>
          </section>

          <!-- Security section -->
          <section v-else-if="activeSection === 'security'" class="ps__section">
            <div class="ps__section-label">{{ t("profileSettings.security") }}</div>
            <label class="ps__field">
              <span>{{ t("profileSettings.currentPassword") }}</span>
              <input v-model="currentPassword" type="password" :disabled="isChangingPassword" />
            </label>
            <label class="ps__field">
              <span>{{ t("profileSettings.newPassword") }}</span>
              <input v-model="newPassword" type="password" :disabled="isChangingPassword" />
            </label>
            <label class="ps__field">
              <span>{{ t("profileSettings.confirmPassword") }}</span>
              <input v-model="confirmPassword" type="password" :disabled="isChangingPassword" />
            </label>
            <div class="ps__section-footer">
              <button
                class="ps__primary-btn"
                type="button"
                :disabled="isChangingPassword || !canChangePassword"
                @click="handleChangePassword"
              >
                {{ isChangingPassword ? t("profileSettings.changingPassword") : t("profileSettings.changePassword") }}
              </button>
            </div>
          </section>

          <!-- Coach section -->
          <section v-else-if="activeSection === 'coach'" class="ps__section">
            <div class="ps__section-label">{{ t("profileSettings.connectCoach") }}</div>
            <label class="ps__field">
              <span>{{ t("profileSettings.coachCodeLabel") }}</span>
              <input
                v-model="coachCode"
                class="ps__mono"
                :placeholder="t('profileSettings.coachCodePlaceholder')"
                :disabled="isRequestingCoach"
              />
            </label>
            <div class="ps__section-footer">
              <button
                class="ps__primary-btn"
                type="button"
                :disabled="isRequestingCoach || !coachCode.trim()"
                @click="handleRequestCoach"
              >
                {{ isRequestingCoach ? t("profileSettings.requestCoachSubmitting") : t("profileSettings.requestCoach") }}
              </button>
            </div>
          </section>

        </div>
      </div>

      <!-- Footer -->
      <div v-if="!isLoading && !errorMessage" class="ps__footer">
        <button class="ps__lang-toggle" type="button" @click="toggleLanguage">
          {{ locale === "cs" ? "EN" : "CS" }}
        </button>
        <button
          v-if="activeSection === 'profile'"
          class="ps__save-btn"
          type="button"
          :disabled="isSaving || !profile"
          @click="save"
        >
          {{ isSaving ? t("profileSettings.saving") : t("profileSettings.save") }}
        </button>
      </div>

    </div>
  </EbModal>
</template>

<style scoped>
:deep(.eb-modal__panel) {
  width: min(100%, 34rem);
}

.ps {
  display: flex;
  flex-direction: column;
  height: min(88vh, 28rem);
}

/* ── Header ────────────────────────────────── */
.ps__header {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.875rem 1rem;
  border-bottom: 1px solid var(--eb-border);
  flex-shrink: 0;
}

.ps__avatar {
  display: inline-grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #1c1c20;
  border: 1px solid #3f3f46;
  color: var(--eb-lime, #c8ff00);
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 700;
  font-size: 11px;
  flex-shrink: 0;
}

.ps__header-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ps__display-name {
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 700;
  font-size: 0.875rem;
  color: var(--eb-text, #fafafa);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ps__role-badge {
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--eb-text-soft, #a1a1aa);
}

.ps__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid var(--eb-border);
  border-radius: 6px;
  background: transparent;
  color: var(--eb-text-muted);
  cursor: pointer;
  flex-shrink: 0;
  transition: color 150ms, border-color 150ms;
}

.ps__close:hover {
  color: var(--eb-text);
  border-color: #52525b;
}

/* ── State ─────────────────────────────────── */
.ps__state {
  padding: 2rem 1.25rem;
  color: var(--eb-text-soft, #a1a1aa);
  font-size: 0.875rem;
}

.ps__state--error {
  color: var(--eb-danger, #f43f5e);
}

/* ── Two-column layout ─────────────────────── */
.ps__layout {
  display: grid;
  grid-template-columns: 9.5rem 1fr;
  flex: 1;
  min-height: 0;
}

/* ── Left nav ──────────────────────────────── */
.ps__nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0.75rem 0.625rem;
  border-right: 1px solid var(--eb-border);
  background: #111113;
  flex-shrink: 0;
}

.ps__nav-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.5rem 0.625rem;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--eb-text-soft, #a1a1aa);
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 600;
  font-size: 0.8125rem;
  text-align: left;
  cursor: pointer;
  transition: background 150ms, color 150ms;
}

.ps__nav-item:hover {
  background: rgba(255, 255, 255, 0.04);
  color: #a1a1aa;
}

.ps__nav-item--active {
  background: rgba(200, 255, 0, 0.07);
  color: var(--eb-lime, #c8ff00);
}

.ps__nav-item--active svg {
  color: var(--eb-lime, #c8ff00);
}

/* ── Right content ─────────────────────────── */
.ps__content {
  padding: 1rem;
}

.ps__section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.ps__section-label {
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: var(--eb-text-soft, #a1a1aa);
  margin-bottom: 0.125rem;
}

/* ── Fields ────────────────────────────────── */
.ps__field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.ps__field span {
  font-size: 0.6875rem;
  color: var(--eb-text-soft, #a1a1aa);
}

.ps__field input {
  width: 100%;
  padding: 0.5rem 0.7rem;
  border: 1px solid var(--eb-border, #27272a);
  border-radius: var(--eb-radius-sm, 6px);
  background: var(--eb-bg, #09090b);
  color: var(--eb-text, #fafafa);
  font: inherit;
  font-size: 0.8125rem;
  transition: border-color 150ms;
}

.ps__field input:focus {
  outline: none;
  border-color: rgba(200, 255, 0, 0.35);
}

.ps__field input:disabled {
  opacity: 0.45;
  cursor: default;
}

.ps__mono {
  font-family: var(--eb-font-mono, 'JetBrains Mono', monospace);
  font-size: 0.8125rem;
  letter-spacing: 0.03em;
}

.ps__section-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 0.25rem;
}

/* Action button inside sections (password, coach) */
.ps__primary-btn {
  height: 34px;
  padding: 0 1rem;
  border: 1px solid rgba(200, 255, 0, 0.35);
  border-radius: var(--eb-radius-sm, 6px);
  background: rgba(200, 255, 0, 0.07);
  color: var(--eb-lime, #c8ff00);
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 700;
  font-size: 0.8125rem;
  white-space: nowrap;
  cursor: pointer;
  transition: background 150ms, border-color 150ms;
}

.ps__primary-btn:hover:not(:disabled) {
  background: rgba(200, 255, 0, 0.13);
  border-color: rgba(200, 255, 0, 0.55);
}

.ps__primary-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

/* ── Footer ────────────────────────────────── */
.ps__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--eb-border);
  flex-shrink: 0;
}

.ps__lang-toggle {
  height: 26px;
  padding: 0 0.75rem;
  border: 1px solid #3f3f46;
  border-radius: 999px;
  background: transparent;
  color: var(--eb-lime, #c8ff00);
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 700;
  font-size: 0.6875rem;
  letter-spacing: 0.08em;
  cursor: pointer;
  transition: border-color 150ms;
}

.ps__lang-toggle:hover {
  border-color: rgba(200, 255, 0, 0.4);
}

.ps__save-btn {
  height: 34px;
  padding: 0 1.125rem;
  border: 1px solid rgba(200, 255, 0, 0.4);
  border-radius: var(--eb-radius-sm, 6px);
  background: rgba(200, 255, 0, 0.08);
  color: var(--eb-lime, #c8ff00);
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 700;
  font-size: 0.8125rem;
  cursor: pointer;
  transition: background 150ms, border-color 150ms;
}

.ps__save-btn:hover:not(:disabled) {
  background: rgba(200, 255, 0, 0.14);
  border-color: rgba(200, 255, 0, 0.55);
}

.ps__save-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

@media (max-width: 540px) {
  .ps__layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }

  .ps__nav {
    flex-direction: row;
    border-right: 0;
    border-bottom: 1px solid var(--eb-border);
    padding: 0.5rem;
    overflow-x: auto;
  }

  .ps__nav-item {
    white-space: nowrap;
  }
}
</style>
