<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { fetchProfileCompletion, saveProfileCompletion, type ProfileCompletionPayload } from "@/api/profile";
import EbButton from "@/components/ui/EbButton.vue";
import EbCard from "@/components/ui/EbCard.vue";
import EbSpinner from "@/components/ui/EbSpinner.vue";
import { useI18n } from "@/composables/useI18n";
import { useAuthStore } from "@/stores/auth";
import { useToastStore } from "@/stores/toasts";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const toastStore = useToastStore();
const { t } = useI18n();

const isLoading = ref(true);
const isSaving = ref(false);
const errorMessage = ref("");
const fieldErrors = ref<Record<string, string[]>>({});
const payload = ref<ProfileCompletionPayload | null>(null);
const form = ref({
  firstName: "",
  lastName: "",
  role: "ATHLETE" as "COACH" | "ATHLETE",
});

const title = computed(() => {
  return form.value.role === "COACH" ? t("profileCompletion.titleCoach") : t("profileCompletion.titleAthlete");
});

async function loadProfileCompletion() {
  isLoading.value = true;
  errorMessage.value = "";
  try {
    const next = typeof route.query.next === "string" ? route.query.next : undefined;
    payload.value = await fetchProfileCompletion(next);
    form.value = {
      firstName: payload.value.first_name,
      lastName: payload.value.last_name,
      role: payload.value.role,
    };
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t("profileCompletion.loadError");
  } finally {
    isLoading.value = false;
  }
}

async function save() {
  isSaving.value = true;
  errorMessage.value = "";
  fieldErrors.value = {};
  try {
    const response = await saveProfileCompletion({
      first_name: form.value.firstName,
      last_name: form.value.lastName,
      role: form.value.role,
      next: payload.value?.next || (typeof route.query.next === "string" ? route.query.next : undefined),
    });
    await authStore.refresh();
    toastStore.push(response.message, "success");
    await router.push(response.redirect_to);
  } catch (error: unknown) {
    const maybeError = error as {
      response?: { data?: { message?: string; errors?: Record<string, string[]> } };
      message?: string;
    };
    fieldErrors.value = maybeError.response?.data?.errors || {};
    errorMessage.value = maybeError.response?.data?.message || maybeError.message || t("profileCompletion.saveError");
    toastStore.push(errorMessage.value, "danger");
  } finally {
    isSaving.value = false;
  }
}

onMounted(() => {
  void loadProfileCompletion();
});
</script>

<template>
  <section class="profile-view">
    <EbCard class="profile-card">
      <div class="profile-card__eyebrow">{{ t("profileCompletion.eyebrow") }}</div>

      <div v-if="isLoading" class="profile-card__loading">
        <EbSpinner />
        <span>{{ t("profileCompletion.loading") }}</span>
      </div>

      <template v-else>
        <h1 class="profile-card__title">{{ title }}</h1>
        <p class="profile-card__text">
          {{ t("profileCompletion.description") }}
        </p>

        <p v-if="errorMessage" class="profile-card__error">{{ errorMessage }}</p>

        <form class="profile-form" @submit.prevent="save">
          <label class="profile-form__field">
            <span class="profile-form__label">{{ t("profileCompletion.firstName") }}</span>
            <input v-model="form.firstName" class="profile-form__input" type="text" maxlength="150" :disabled="isSaving" />
            <span v-if="fieldErrors.first_name?.length" class="profile-form__error">{{ fieldErrors.first_name[0] }}</span>
          </label>

          <label class="profile-form__field">
            <span class="profile-form__label">{{ t("profileCompletion.lastName") }}</span>
            <input v-model="form.lastName" class="profile-form__input" type="text" maxlength="150" :disabled="isSaving" />
            <span v-if="fieldErrors.last_name?.length" class="profile-form__error">{{ fieldErrors.last_name[0] }}</span>
          </label>

          <label class="profile-form__field profile-form__field--wide">
            <span class="profile-form__label">{{ t("profileCompletion.role") }}</span>
            <select v-model="form.role" class="profile-form__input" :disabled="isSaving">
              <option v-for="option in payload?.role_options || []" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
            <span v-if="fieldErrors.role?.length" class="profile-form__error">{{ fieldErrors.role[0] }}</span>
          </label>

          <div class="profile-form__actions">
            <EbButton :disabled="isSaving">
              {{ isSaving ? t("profileCompletion.saving") : t("profileCompletion.save") }}
            </EbButton>
          </div>
        </form>
      </template>
    </EbCard>
  </section>
</template>

<style scoped>
.profile-view {
  display: grid;
}

.profile-card {
  padding: 1.5rem;
}

.profile-card__eyebrow {
  color: var(--eb-text-muted);
  font-size: var(--eb-type-label-size);
  font-weight: 600;
  letter-spacing: var(--eb-type-label-tracking);
  text-transform: uppercase;
}

.profile-card__title {
  margin: 0.75rem 0 0;
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-h1-size);
  font-weight: var(--eb-type-h1-weight);
  line-height: var(--eb-type-h1-line);
  letter-spacing: var(--eb-type-h1-tracking);
}

.profile-card__text {
  max-width: 38rem;
  color: var(--eb-text-soft);
  font-size: var(--eb-type-body-size);
  line-height: var(--eb-type-body-line);
}

.profile-card__loading,
.profile-form {
  display: grid;
  gap: 1rem;
}

.profile-card__loading {
  align-items: center;
  justify-items: start;
  margin-top: 1rem;
  color: var(--eb-text-soft);
  font-size: var(--eb-type-body-size);
}

.profile-card__error,
.profile-form__error {
  color: var(--eb-danger);
  font-size: var(--eb-type-small-size);
}

.profile-form {
  max-width: 38rem;
  margin-top: 1.5rem;
}

.profile-form__field {
  display: grid;
  gap: 0.45rem;
}

.profile-form__field--wide {
  max-width: 18rem;
}

.profile-form__label {
  color: var(--eb-text-muted);
  font-size: var(--eb-type-label-size);
  font-weight: 600;
  letter-spacing: var(--eb-type-label-tracking);
  text-transform: uppercase;
}

.profile-form__input {
  width: 100%;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-sm);
  background: var(--eb-bg);
  color: var(--eb-text);
  padding: 0.75rem 0.85rem;
}

.profile-form__input:focus {
  outline: none;
  border-color: rgba(200, 255, 0, 0.4);
  box-shadow: var(--eb-glow-lime);
}

.profile-form__actions {
  display: flex;
  justify-content: flex-start;
  margin-top: 0.5rem;
}
</style>
