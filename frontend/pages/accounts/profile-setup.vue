<script setup lang="ts">
import AuthPreviewShell from "@/components/auth/AuthPreviewShell.vue"
import { profileSetup } from "~/utils/api/auth"
import { useAuthStore } from "@/stores/auth"

definePageMeta({ layout: "auth" })

const authStore = useAuthStore()

if (!authStore.user) {
  await navigateTo("/accounts/login/")
} else if (!authStore.user.needs_profile_setup) {
  await navigateTo(authStore.user.default_app_route || "/app/dashboard")
}

const form = reactive({
  firstName: authStore.user?.first_name ?? "",
  lastName: authStore.user?.last_name ?? "",
  role: "ATHLETE" as "COACH" | "ATHLETE",
  termsAccepted: false,
})

const isSubmitting = ref(false)
const formError = ref("")
const fieldErrors = ref<Record<string, string[]>>({})

function firstError(name: string) {
  return fieldErrors.value[name]?.[0] || ""
}

async function submit() {
  isSubmitting.value = true
  formError.value = ""
  fieldErrors.value = {}
  try {
    const response = await profileSetup({
      first_name: form.firstName,
      last_name: form.lastName,
      role: form.role,
      terms_accepted: form.termsAccepted,
    })
    await authStore.refresh()
    const isExternal = response.redirect_to.startsWith("http")
    await navigateTo(response.redirect_to, isExternal ? { external: true } : undefined)
  } catch (error: unknown) {
    const maybeError = error as { data?: { message?: string; errors?: Record<string, string[]> } }
    formError.value = maybeError.data?.message || "Nastavení profilu se nepodařilo uložit."
    fieldErrors.value = maybeError.data?.errors || {}
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <main class="auth-flow-page">
    <div class="auth-flow-page__wrap">
      <AuthPreviewShell
        brand-eyebrow="Onboarding"
        brand-title="Jeden krok před vstupem do aplikace."
        brand-description="Nastav svou roli a potvrď souhlas s podmínkami. Zabere to méně než minutu."
        :stats="[
          { icon: '🏃', label: 'Pro sportovce', value: 'Plán · Trénink · Analýza' },
          { icon: '🎯', label: 'Pro trenéry', value: 'Skupiny · Plány · Přehled', blue: true },
        ]"
      >
        <div class="auth-flow-card">
          <div class="auth-flow-card__eyebrow">Profile Setup</div>
          <h1>Nastav svůj profil</h1>
          <p>Přihlásil(a) ses přes Google. Dokonči nastavení účtu.</p>

          <div class="auth-flow-grid">
            <label class="auth-flow-field">
              <span>Jméno</span>
              <input v-model="form.firstName" type="text" autocomplete="given-name" />
              <small v-if="firstError('first_name')" class="is-danger">{{ firstError("first_name") }}</small>
            </label>
            <label class="auth-flow-field">
              <span>Příjmení</span>
              <input v-model="form.lastName" type="text" autocomplete="family-name" />
              <small v-if="firstError('last_name')" class="is-danger">{{ firstError("last_name") }}</small>
            </label>
          </div>

          <div class="auth-flow-field">
            <span>Jsem</span>
            <div class="auth-role-grid">
              <button
                type="button"
                class="auth-role-card"
                :class="{ 'auth-role-card--active-lime': form.role === 'ATHLETE' }"
                @click="form.role = 'ATHLETE'"
              >
                <span class="auth-role-card__dot auth-role-card__dot--lime"></span>
                <span class="auth-role-card__name">Sportovec</span>
                <span class="auth-role-card__desc">Plánuji a zapisuji tréninky</span>
              </button>
              <button
                type="button"
                class="auth-role-card"
                :class="{ 'auth-role-card--active-blue': form.role === 'COACH' }"
                @click="form.role = 'COACH'"
              >
                <span class="auth-role-card__dot auth-role-card__dot--blue"></span>
                <span class="auth-role-card__name">Trenér</span>
                <span class="auth-role-card__desc">Vedu atlety a připravuji plány</span>
              </button>
            </div>
            <small v-if="firstError('role')" class="is-danger">{{ firstError("role") }}</small>
          </div>

          <label class="auth-flow-check auth-flow-check--terms">
            <input v-model="form.termsAccepted" type="checkbox" />
            <span>
              Souhlasím s
              <a href="/terms" target="_blank" rel="noopener">Podmínkami použití</a>
              a
              <a href="/privacy" target="_blank" rel="noopener">Ochranou osobních údajů</a>
            </span>
          </label>
          <small v-if="firstError('terms_accepted')" class="is-danger">{{ firstError("terms_accepted") }}</small>

          <p v-if="formError" class="auth-flow-error">{{ formError }}</p>

          <button
            class="auth-flow-button auth-flow-button--primary"
            type="button"
            :disabled="isSubmitting || !form.termsAccepted"
            @click="submit"
          >
            {{ isSubmitting ? "Ukládám..." : "Pokračovat do aplikace" }}
          </button>
        </div>
      </AuthPreviewShell>
    </div>
  </main>
</template>

<style scoped>
.auth-flow-page {
  min-height: 100vh;
  padding: 1.5rem 1rem 2.5rem;
  background:
    radial-gradient(circle at top right, rgba(200, 255, 0, 0.12), transparent 20rem),
    radial-gradient(circle at bottom left, rgba(56, 189, 248, 0.1), transparent 22rem),
    linear-gradient(180deg, #0c0c10 0%, var(--eb-bg) 100%);
}

.auth-flow-page__wrap {
  width: min(100%, 88rem);
  margin: 0 auto;
}

.auth-flow-card {
  display: grid;
  gap: 1rem;
}

.auth-flow-card__eyebrow {
  color: var(--eb-text-muted);
  font-size: var(--eb-type-label-size);
  font-weight: 700;
  letter-spacing: var(--eb-type-label-tracking);
  text-transform: uppercase;
}

.auth-flow-card h1 {
  margin: 0;
  font-family: var(--eb-font-display);
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.03em;
}

.auth-flow-card p {
  margin: 0;
  color: var(--eb-text-soft);
  font-size: 0.875rem;
  line-height: 1.55;
}

.auth-flow-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.65rem;
  width: 100%;
  min-height: 3rem;
  padding: 0 1rem;
  border: 1px solid transparent;
  border-radius: 0.7rem;
  font-size: var(--eb-type-small-size);
  font-weight: 700;
  letter-spacing: 0.02em;
  transition: transform 160ms ease, background 160ms ease;
}

.auth-flow-button:hover { transform: translateY(-1px); }

.auth-flow-button--primary {
  background: var(--eb-lime);
  color: #09090b;
  box-shadow: var(--eb-glow-lime);
}

.auth-flow-button--primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  transform: none;
}

.auth-flow-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.auth-flow-field {
  display: grid;
  gap: 0.45rem;
}

.auth-flow-field span,
.auth-flow-field > span:first-child {
  color: var(--eb-text-muted);
  font-size: var(--eb-type-label-size);
  font-weight: 700;
  letter-spacing: var(--eb-type-label-tracking);
  text-transform: uppercase;
}

.auth-flow-field input {
  width: 100%;
  min-height: 3rem;
  border: 1px solid var(--eb-border);
  border-radius: 0.7rem;
  padding: 0.8rem 0.9rem;
  background: #09090b;
  color: var(--eb-text);
}

.auth-flow-field input:focus {
  outline: none;
  border-color: rgba(200, 255, 0, 0.36);
  box-shadow: var(--eb-glow-lime);
}

.auth-flow-field small.is-danger,
.auth-flow-error {
  color: #fda4af;
  font-size: var(--eb-type-small-size);
  margin: 0;
}

.auth-flow-check {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  color: var(--eb-text-soft);
  font-size: var(--eb-type-small-size);
}

.auth-flow-check--terms a {
  color: var(--eb-lime);
  font-weight: 600;
  text-decoration: none;
}

.auth-flow-check--terms a:hover {
  text-decoration: underline;
}

.auth-role-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.625rem;
}

.auth-role-card {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 0.875rem;
  border-radius: 0.75rem;
  border: 1px solid var(--eb-border);
  background: var(--eb-bg);
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s, background 0.15s;
}

.auth-role-card:hover { border-color: rgba(255, 255, 255, 0.14); }

.auth-role-card--active-lime {
  border-color: rgba(200, 255, 0, 0.28);
  background: linear-gradient(180deg, rgba(200, 255, 0, 0.07) 0%, transparent 100%);
}

.auth-role-card--active-blue {
  border-color: rgba(56, 189, 248, 0.28);
  background: linear-gradient(180deg, rgba(56, 189, 248, 0.07) 0%, transparent 100%);
}

.auth-role-card__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.auth-role-card__dot--lime { background: var(--eb-lime); }
.auth-role-card__dot--blue { background: var(--eb-blue); }

.auth-role-card__name {
  font-size: 0.8125rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--eb-text);
}

.auth-role-card__desc {
  font-size: 0.6875rem;
  color: var(--eb-text-muted);
  line-height: 1.4;
}

@media (max-width: 720px) {
  .auth-flow-page { padding-inline: 0.75rem; }
  .auth-flow-grid { grid-template-columns: 1fr; }
}
</style>
