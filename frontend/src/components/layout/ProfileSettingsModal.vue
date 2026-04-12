<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { changePassword } from "@/api/auth";
import { requestCoachByCode } from "@/api/coach";
import { fetchProfileSettings, saveProfileSettings, type ProfileSettingsPayload } from "@/api/profile";
import EbButton from "@/components/ui/EbButton.vue";
import EbModal from "@/components/ui/EbModal.vue";
import { useI18n } from "@/composables/useI18n";
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

// Password change
const currentPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");
const isChangingPassword = ref(false);

// Coach connection
const coachCode = ref("");
const isRequestingCoach = ref(false);

const roleLabel = computed(() => {
  if (profile.value?.role === "COACH") {
    return t("profileSettings.roleCoach");
  }
  return t("profileSettings.roleAthlete");
});

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
  if (profile.value) {
    profile.value = {
      ...profile.value,
      language: locale.value,
    };
  }
}

async function handleChangePassword() {
  if (!currentPassword.value || !newPassword.value || !confirmPassword.value) return;
  isChangingPassword.value = true;
  try {
    await changePassword(currentPassword.value, newPassword.value, confirmPassword.value);
    toastStore.push(t("profileSettings.changePasswordSuccess"), "success");
    currentPassword.value = "";
    newPassword.value = "";
    confirmPassword.value = "";
  } catch (error) {
    toastStore.push(error instanceof Error ? error.message : t("profileSettings.changePasswordError"), "danger");
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
    <div class="profile-settings">
      <div class="profile-settings__header">
        <div>
          <div class="profile-settings__eyebrow">{{ t("profileSettings.eyebrow") }}</div>
          <h2 class="profile-settings__title">{{ t("profileSettings.title") }}</h2>
        </div>
        <EbButton variant="ghost" @click="emit('close')">{{ t("profileSettings.close") }}</EbButton>
      </div>

      <div v-if="isLoading" class="profile-settings__state">{{ t("profileSettings.loading") }}</div>

      <div v-else-if="errorMessage" class="profile-settings__state profile-settings__state--error">
        {{ errorMessage }}
      </div>

      <div v-else-if="profile" class="profile-settings__body">
        <section class="profile-settings__panel">
          <div class="profile-settings__panel-title">{{ t("profileSettings.identity") }}</div>
          <div class="profile-settings__grid">
            <label class="profile-settings__field">
              <span>{{ t("profileSettings.firstName") }}</span>
              <input v-model="firstName" :disabled="isSaving" />
            </label>
            <label class="profile-settings__field">
              <span>{{ t("profileSettings.lastName") }}</span>
              <input v-model="lastName" :disabled="isSaving" />
            </label>
            <label class="profile-settings__field profile-settings__field--wide">
              <span>{{ t("profileSettings.email") }}</span>
              <input :value="profile.email" disabled />
            </label>
          </div>
        </section>

        <section class="profile-settings__panel">
          <div class="profile-settings__panel-title">{{ t("profileSettings.workspace") }}</div>
          <div class="profile-settings__meta">
            <div class="profile-settings__meta-row">
              <span>{{ t("profileSettings.role") }}</span>
              <strong>{{ roleLabel }}</strong>
            </div>
            <div class="profile-settings__meta-row">
              <span>{{ t("profileSettings.defaultRoute") }}</span>
              <a :href="profile.default_app_route">{{ profile.default_app_route }}</a>
            </div>
            <div class="profile-settings__meta-row">
              <span>{{ t("profileSettings.language") }}</span>
              <button class="profile-settings__lang-toggle" type="button" @click="toggleLanguage">
                {{ locale === "cs" ? "EN" : "CS" }}
              </button>
            </div>
          </div>
        </section>

        <section class="profile-settings__panel">
          <div class="profile-settings__panel-title">{{ t("profileSettings.security") }}</div>
          <div class="profile-settings__grid">
            <label class="profile-settings__field">
              <span>{{ t("profileSettings.currentPassword") }}</span>
              <input v-model="currentPassword" type="password" :disabled="isChangingPassword" />
            </label>
            <label class="profile-settings__field">
              <span>{{ t("profileSettings.newPassword") }}</span>
              <input v-model="newPassword" type="password" :disabled="isChangingPassword" />
            </label>
            <label class="profile-settings__field profile-settings__field--wide">
              <span>{{ t("profileSettings.confirmPassword") }}</span>
              <input v-model="confirmPassword" type="password" :disabled="isChangingPassword" />
            </label>
          </div>
          <div class="profile-settings__panel-footer">
            <EbButton
              variant="secondary"
              :disabled="isChangingPassword || !currentPassword || !newPassword || !confirmPassword"
              @click="handleChangePassword"
            >
              {{ isChangingPassword ? t("profileSettings.changingPassword") : t("profileSettings.changePassword") }}
            </EbButton>
          </div>
        </section>

        <section v-if="profile.role === 'ATHLETE'" class="profile-settings__panel">
          <div class="profile-settings__panel-title">{{ t("profileSettings.connectCoach") }}</div>
          <div class="profile-settings__request-row">
            <label class="profile-settings__field" style="flex: 1">
              <span>{{ t("profileSettings.coachCodeLabel") }}</span>
              <input
                v-model="coachCode"
                class="profile-settings__mono-input"
                :placeholder="t('profileSettings.coachCodePlaceholder')"
                :disabled="isRequestingCoach"
              />
            </label>
            <EbButton
              variant="secondary"
              :disabled="isRequestingCoach || !coachCode.trim()"
              @click="handleRequestCoach"
            >
              {{ isRequestingCoach ? t("profileSettings.requestCoachSubmitting") : t("profileSettings.requestCoach") }}
            </EbButton>
          </div>
        </section>

        <div class="profile-settings__footer">
          <EbButton variant="ghost" :disabled="isSaving" @click="emit('close')">{{ t("profileSettings.cancel") }}</EbButton>
          <EbButton :disabled="isSaving" @click="save">{{ isSaving ? t("profileSettings.saving") : t("profileSettings.save") }}</EbButton>
        </div>
      </div>
    </div>
  </EbModal>
</template>

<style scoped>
.profile-settings {
  display: flex;
  flex-direction: column;
  max-height: min(88vh, 50rem);
}

.profile-settings__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.25rem 1.5rem 1rem;
  border-bottom: 1px solid var(--eb-border);
}

.profile-settings__eyebrow {
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.profile-settings__title {
  margin: 0.45rem 0 0;
  font-family: var(--eb-font-display);
  font-size: 1.3rem;
}

.profile-settings__state {
  padding: 2rem 1.5rem;
  color: var(--eb-text-soft);
  font-size: 0.875rem;
}

.profile-settings__state--error {
  color: var(--eb-danger);
}

.profile-settings__body {
  display: grid;
  gap: 1rem;
  padding: 1rem 1.5rem 1.5rem;
  overflow-y: auto;
}

.profile-settings__panel {
  display: grid;
  gap: 0.85rem;
  padding: 1rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-md);
  background: var(--eb-bg-elevated);
}

.profile-settings__panel-title {
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.profile-settings__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.85rem;
}

.profile-settings__field {
  display: grid;
  gap: 0.4rem;
}

.profile-settings__field--wide {
  grid-column: 1 / -1;
}

.profile-settings__field span {
  color: var(--eb-text-muted);
  font-size: 0.75rem;
}

.profile-settings__field input {
  width: 100%;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-sm);
  background: var(--eb-bg);
  color: var(--eb-text);
  padding: 0.75rem 0.85rem;
  font: inherit;
}

.profile-settings__meta {
  display: grid;
  gap: 0.75rem;
}

.profile-settings__meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  color: var(--eb-text-soft);
  font-size: 0.875rem;
}

.profile-settings__meta-row strong,
.profile-settings__meta-row a {
  color: var(--eb-text);
  font-family: var(--eb-font-mono);
  font-size: 0.8125rem;
}

.profile-settings__lang-toggle {
  min-width: 3rem;
  padding: 0.35rem 0.65rem;
  border: 1px solid var(--eb-border);
  border-radius: 999px;
  background: transparent;
  color: var(--eb-lime);
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.profile-settings__panel-footer {
  display: flex;
  justify-content: flex-end;
}

.profile-settings__request-row {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
}

.profile-settings__mono-input {
  width: 100%;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-sm);
  background: var(--eb-bg);
  color: var(--eb-text);
  font-family: var(--eb-font-mono);
  font-size: var(--eb-type-mono-size);
  letter-spacing: var(--eb-type-mono-tracking);
  padding: 0.75rem 0.85rem;
}

.profile-settings__footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding-top: 0.25rem;
}

@media (max-width: 767px) {
  .profile-settings__header,
  .profile-settings__body {
    padding-inline: 1rem;
  }

  .profile-settings__grid {
    grid-template-columns: 1fr;
  }

  .profile-settings__meta-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .profile-settings__footer {
    flex-direction: column-reverse;
  }

  .profile-settings__request-row {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
