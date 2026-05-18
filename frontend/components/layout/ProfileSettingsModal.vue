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

const roleLabel = computed(() => {
  if (profile.value?.role === "COACH") return t("profileSettings.roleCoach");
  return t("profileSettings.roleAthlete");
});

const canChangePassword = computed(
  () => !!(currentPassword.value && newPassword.value && confirmPassword.value),
);

watch(
  () => props.open,
  async (open) => {
    if (!open) {
      errorMessage.value = "";
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

      <!-- Loading / Error -->
      <div v-if="isLoading" class="ps__state">{{ t("profileSettings.loading") }}</div>
      <div v-else-if="errorMessage" class="ps__state ps__state--error">{{ errorMessage }}</div>

      <div v-else-if="profile" class="ps__body">
        <!-- Profile -->
        <section class="ps__section">
          <div class="ps__section-label">{{ t("profileSettings.identity") }}</div>
          <div class="ps__two-col">
            <label class="ps__field">
              <span>{{ t("profileSettings.firstName") }}</span>
              <input v-model="firstName" :disabled="isSaving" />
            </label>
            <label class="ps__field">
              <span>{{ t("profileSettings.lastName") }}</span>
              <input v-model="lastName" :disabled="isSaving" />
            </label>
          </div>
          <label class="ps__field">
            <span>{{ t("profileSettings.email") }}</span>
            <input :value="profile.email" disabled />
          </label>
        </section>

        <!-- Password -->
        <section class="ps__section">
          <div class="ps__section-label">{{ t("profileSettings.security") }}</div>
          <div class="ps__two-col">
            <label class="ps__field">
              <span>{{ t("profileSettings.currentPassword") }}</span>
              <input v-model="currentPassword" type="password" :disabled="isChangingPassword" />
            </label>
            <label class="ps__field">
              <span>{{ t("profileSettings.newPassword") }}</span>
              <input v-model="newPassword" type="password" :disabled="isChangingPassword" />
            </label>
          </div>
          <div class="ps__inline-row">
            <label class="ps__field" style="flex: 1">
              <span>{{ t("profileSettings.confirmPassword") }}</span>
              <input v-model="confirmPassword" type="password" :disabled="isChangingPassword" />
            </label>
            <button
              class="ps__action-btn"
              type="button"
              :disabled="isChangingPassword || !canChangePassword"
              @click="handleChangePassword"
            >
              {{ isChangingPassword ? t("profileSettings.changingPassword") : t("profileSettings.changePassword") }}
            </button>
          </div>
        </section>

        <!-- Connect coach (athletes only) -->
        <section v-if="profile.role === 'ATHLETE'" class="ps__section">
          <div class="ps__section-label">{{ t("profileSettings.connectCoach") }}</div>
          <div class="ps__inline-row">
            <label class="ps__field" style="flex: 1">
              <span>{{ t("profileSettings.coachCodeLabel") }}</span>
              <input
                v-model="coachCode"
                class="ps__mono"
                :placeholder="t('profileSettings.coachCodePlaceholder')"
                :disabled="isRequestingCoach"
              />
            </label>
            <button
              class="ps__action-btn"
              type="button"
              :disabled="isRequestingCoach || !coachCode.trim()"
              @click="handleRequestCoach"
            >
              {{ isRequestingCoach ? t("profileSettings.requestCoachSubmitting") : t("profileSettings.requestCoach") }}
            </button>
          </div>
        </section>
      </div>

      <!-- Footer -->
      <div class="ps__footer">
        <button class="ps__lang-toggle" type="button" @click="toggleLanguage">
          {{ locale === "cs" ? "EN" : "CS" }}
        </button>
        <button
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
/* Override modal panel width to popup size */
:deep(.eb-modal__panel) {
  width: min(100%, 30rem);
}

.ps {
  display: flex;
  flex-direction: column;
  max-height: min(90vh, 44rem);
}

/* ── Header ──────────────────────────────────── */
.ps__header {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 1rem 1.125rem;
  border-bottom: 1px solid var(--eb-border);
  flex-shrink: 0;
}

.ps__avatar {
  display: inline-grid;
  place-items: center;
  width: 36px;
  height: 36px;
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
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
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
  color: var(--eb-text-muted, #71717a);
  letter-spacing: 0.04em;
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
  transition: color 150ms ease-out, border-color 150ms ease-out;
}

.ps__close:hover {
  color: var(--eb-text);
  border-color: #52525b;
}

/* ── State ───────────────────────────────────── */
.ps__state {
  padding: 2rem 1.25rem;
  color: var(--eb-text-muted);
  font-size: 0.875rem;
}

.ps__state--error {
  color: var(--eb-danger, #f43f5e);
}

/* ── Body ────────────────────────────────────── */
.ps__body {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

/* ── Sections ────────────────────────────────── */
.ps__section {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  padding: 1rem 1.125rem;
  border-bottom: 1px solid var(--eb-border);
}

.ps__section-label {
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: var(--eb-text-muted, #71717a);
  margin-bottom: 0.125rem;
}

/* ── Fields ──────────────────────────────────── */
.ps__two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.625rem;
}

.ps__field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.ps__field span {
  font-size: 0.6875rem;
  color: var(--eb-text-muted, #71717a);
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
  transition: border-color 150ms ease-out;
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

/* ── Inline row (confirm + button / code + button) */
.ps__inline-row {
  display: flex;
  align-items: flex-end;
  gap: 0.625rem;
}

.ps__action-btn {
  flex-shrink: 0;
  height: 34px;
  padding: 0 0.875rem;
  border: 1px solid #3f3f46;
  border-radius: var(--eb-radius-sm, 6px);
  background: transparent;
  color: var(--eb-text-muted, #71717a);
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 700;
  font-size: 0.75rem;
  white-space: nowrap;
  cursor: pointer;
  transition: border-color 150ms ease-out, color 150ms ease-out;
}

.ps__action-btn:hover:not(:disabled) {
  border-color: #52525b;
  color: var(--eb-text, #fafafa);
}

.ps__action-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

/* ── Footer ──────────────────────────────────── */
.ps__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.875rem 1.125rem;
  border-top: 1px solid var(--eb-border);
  flex-shrink: 0;
}

.ps__lang-toggle {
  height: 28px;
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
  transition: border-color 150ms ease-out;
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
  transition: background 150ms ease-out, border-color 150ms ease-out;
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
  .ps__two-col {
    grid-template-columns: 1fr;
  }

  .ps__inline-row {
    flex-direction: column;
    align-items: stretch;
  }

  .ps__action-btn {
    height: 38px;
  }
}
</style>
