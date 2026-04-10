<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { acceptInvite, fetchInvite } from "@/api/invites";
import type { InviteDetail } from "@/api/invites";
import EbButton from "@/components/ui/EbButton.vue";
import EbCard from "@/components/ui/EbCard.vue";
import EbSpinner from "@/components/ui/EbSpinner.vue";
import AppShell from "@/components/layout/AppShell.vue";
import { useI18n } from "@/composables/useI18n";

const route = useRoute();
const router = useRouter();
const { t } = useI18n();
const token = route.params.token as string;

const isLoading = ref(true);
const isAccepting = ref(false);
const accepted = ref(false);
const errorMessage = ref("");
const invite = ref<InviteDetail | null>(null);

onMounted(async () => {
  try {
    invite.value = await fetchInvite(token);
  } catch {
    errorMessage.value = t("invite.notFound");
  } finally {
    isLoading.value = false;
  }
});

async function accept() {
  isAccepting.value = true;
  try {
    await acceptInvite(token);
    accepted.value = true;
    setTimeout(() => void router.push("/app/dashboard"), 2000);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : t("invite.error");
  } finally {
    isAccepting.value = false;
  }
}
</script>

<template>
  <AppShell variant="athlete">
    <div class="invite-view">
      <EbCard class="invite-card">
        <div v-if="isLoading" class="invite-card__loading">
          <EbSpinner />
          <span>{{ t("invite.loading") }}</span>
        </div>

        <template v-else>
          <h1 class="invite-card__title">{{ t("invite.title") }}</h1>

          <div v-if="errorMessage" class="invite-card__error">{{ errorMessage }}</div>

          <template v-else-if="invite">
            <div v-if="accepted" class="invite-card__accepted">{{ t("invite.accepted") }}</div>

            <template v-else-if="invite.is_used">
              <p class="invite-card__message">{{ t("invite.used") }}</p>
            </template>

            <template v-else-if="invite.is_expired">
              <p class="invite-card__message">{{ t("invite.expired") }}</p>
            </template>

            <template v-else>
              <p class="invite-card__detail">{{ t("invite.group", { name: invite.group_name }) }}</p>
              <p class="invite-card__detail">{{ t("invite.coach", { name: invite.coach_name }) }}</p>
              <EbButton :disabled="isAccepting" @click="accept">
                {{ isAccepting ? t("invite.accepting") : t("invite.accept") }}
              </EbButton>
            </template>
          </template>
        </template>
      </EbCard>
    </div>
  </AppShell>
</template>

<style scoped>
.invite-view {
  display: grid;
  place-items: center;
  min-height: calc(100vh - var(--eb-topnav-height) - 4rem);
}

.invite-card {
  width: min(90vw, 400px);
  padding: 2rem;
  display: grid;
  gap: 1rem;
}

.invite-card__title {
  margin: 0;
  font-family: var(--eb-font-display);
  font-size: 1.5rem;
}

.invite-card__loading {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--eb-text-soft);
}

.invite-card__detail {
  margin: 0;
  color: var(--eb-text-soft);
  font-size: 0.9375rem;
}

.invite-card__error,
.invite-card__message {
  margin: 0;
  color: var(--eb-text-soft);
  font-size: 0.9375rem;
}

.invite-card__error {
  color: var(--eb-danger);
}

.invite-card__accepted {
  color: var(--eb-lime);
  font-weight: 600;
}
</style>
