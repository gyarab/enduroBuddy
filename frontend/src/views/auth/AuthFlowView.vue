<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import AuthPreviewShell from "@/components/auth/AuthPreviewShell.vue";
import {
  confirmEmailKey,
  changePassword,
  disconnectSocialAccount,
  fetchEmailAddresses,
  fetchEmailConfirmState,
  loginWithPassword,
  logoutFromSession,
  fetchPasswordSetState,
  fetchPasswordResetKeyState,
  fetchReauthenticateState,
  fetchSocialConnections,
  mutateEmailAddress,
  requestPasswordReset,
  setPassword,
  submitReauthenticate,
  submitPasswordResetFromKey,
  signupWithPassword,
} from "@/api/auth";
import { useAuthStore } from "@/stores/auth";

type AuthScreen =
  | "login"
  | "signup"
  | "password-reset"
  | "password-reset-done"
  | "password-reset-key"
  | "password-reset-key-done"
  | "verification-sent"
  | "email-confirm-key"
  | "email-management"
  | "password-change"
  | "password-set"
  | "reauthenticate"
  | "logout"
  | "inactive"
  | "social-error"
  | "social-cancelled"
  | "connections";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const isSubmitting = ref(false);
const formError = ref("");
const fieldErrors = ref<Record<string, string[]>>({});

const loginForm = reactive({
  email: "",
  password: "",
  remember: true,
});

const signupForm = reactive({
  firstName: "",
  lastName: "",
  email: "",
  role: "ATHLETE" as "COACH" | "ATHLETE",
  password: "",
  passwordConfirmation: "",
});

const resetForm = reactive({
  email: "",
});

const resetKeyForm = reactive({
  password: "",
  passwordConfirmation: "",
});

const emailManagementState = ref<{
  isLoading: boolean;
  canAddEmail: boolean;
  emails: Array<{
    email: string;
    verified: boolean;
    primary: boolean;
    can_delete: boolean;
    can_mark_primary: boolean;
  }>;
}>({
  isLoading: false,
  canAddEmail: false,
  emails: [],
});

const emailAddForm = reactive({
  newEmail: "",
});

const passwordChangeForm = reactive({
  currentPassword: "",
  password: "",
  passwordConfirmation: "",
});

const passwordSetForm = reactive({
  password: "",
  passwordConfirmation: "",
});

const passwordSetState = ref({
  isLoading: false,
  hasUsablePassword: false,
});

const socialConnectionsState = ref<{
  isLoading: boolean;
  accounts: Array<{
    id: number;
    provider: string;
    provider_name: string;
    brand_name: string;
    label: string;
    uid: string;
  }>;
  connectGoogleUrl: string;
}>({
  isLoading: false,
  accounts: [],
  connectGoogleUrl: "/accounts/google/login/?process=connect",
});

const reauthenticateState = ref({
  isLoading: false,
  next: "",
});

const reauthenticateForm = reactive({
  password: "",
});

const emailConfirmState = ref<{
  isLoading: boolean;
  canConfirm: boolean;
  email: string;
  userDisplay: string;
  message: string;
}>({
  isLoading: false,
  canConfirm: false,
  email: "",
  userDisplay: "",
  message: "",
});

const passwordResetKeyState = ref<{
  isLoading: boolean;
  tokenValid: boolean;
  message: string;
}>({
  isLoading: false,
  tokenValid: true,
  message: "",
});

const screen = computed<AuthScreen>(() => {
  const value = String(route.meta.authScreen || "login");
  return value as AuthScreen;
});

const shellConfig = computed(() => {
  switch (screen.value) {
    case "signup":
      return {
        eyebrow: "Start Clean",
        title: "Začni plánovat s přesností od prvního dne.",
        description: "Registrace je rychlá a už během prvního kroku je jasné, jestli vstupuješ jako coach nebo athlete.",
        statLabel: "Fast path",
        statValue: "Google First",
        statDescription: "Social signup je preferovaný vstup, role a heslo mají jasné místo bez vizuálního šumu.",
      };
    case "password-reset":
      return {
        eyebrow: "Recovery",
        title: "Vrátíme tě zpět bez tření.",
        description: "Recovery stránky jsou méně marketingové a víc utilitární. Jedna úloha, jedna akce, jeden klidný výsledek.",
        statLabel: "Secure Reset",
        statValue: "Email Link",
        statDescription: "Support copy vysvětluje, že obnovovací odkaz pošleme jen pokud účet pro daný e-mail existuje.",
      };
    case "password-reset-done":
      return {
        eyebrow: "Recovery",
        title: "Reset link je na cestě.",
        description: "Pokud účet existuje, poslali jsme odkaz pro obnovu hesla. Zbytek flow může proběhnout klidně mimo aplikaci.",
        statLabel: "Next step",
        statValue: "Check Email",
        statDescription: "Držíme stejný shell i pro mezistavy, aby auth nepůsobil rozpadle.",
      };
    case "password-reset-key":
      return {
        eyebrow: "Recovery",
        title: "Bezpečné nastavení nového hesla.",
        description: "Link z e-mailu držíme v tom samém auth shellu a po validaci necháme uživatele heslo změnit přímo ve Vue flow.",
        statLabel: "Key Flow",
        statValue: "Validated",
        statDescription: "Když je odkaz neplatný, stejná obrazovka se jen přepne do error stavu.",
      };
    case "password-reset-key-done":
      return {
        eyebrow: "Recovery",
        title: "Heslo je změněné a cesta zpět je jasná.",
        description: "Po úspěšné změně hesla zůstáváme ve stejném auth jazyce a vracíme uživatele přirozeně na login.",
        statLabel: "Done",
        statValue: "Password Updated",
        statDescription: "Bez bootstrap fallbacku nebo skoku na jinou vizuální vrstvu.",
      };
    case "verification-sent":
      return {
        eyebrow: "Email Verification",
        title: "Potvrzení e-mailu je další čistý krok v auth flow.",
        description: "Po registraci držíme uživatele ve stejném designu a jasně vysvětlíme, co se stane dál.",
        statLabel: "Next step",
        statValue: "Check Inbox",
        statDescription: "Po potvrzení e-mailu se uživatel vrátí zpět do aplikace bez vizuálního skoku.",
      };
    case "email-confirm-key":
      return {
        eyebrow: "Email Verification",
        title: "Potvrzení e-mailu jako finální krok bez vizuálního zlomu.",
        description: "Ověřovací link z e-mailu je teď obsloužený stejným Vue auth shellem jako login a signup.",
        statLabel: "Verification",
        statValue: "Key Based",
        statDescription: "Validní i nevalidní odkaz mají jasný a konzistentní stav.",
      };
    case "email-management":
      return {
        eyebrow: "Account Email",
        title: "Správa e-mailů ve stejném auth jazyce.",
        description: "Primární, ověřené i čekající e-maily teď běží v tom samém Vue modulu jako login a signup.",
        statLabel: "Email Management",
        statValue: "Unified",
        statDescription: "Přidání, resend verification, primary i remove jsou napojené na backend API.",
      };
    case "password-change":
      return {
        eyebrow: "Security",
        title: "Změna hesla bez návratu ke starým template.",
        description: "Když má uživatel heslo, může ho změnit ve stejném auth shellu a pořád zůstává v rámci SPA.",
        statLabel: "Security",
        statValue: "Change Password",
        statDescription: "Používáme stejná validační pravidla jako allauth formuláře.",
      };
    case "password-set":
      return {
        eyebrow: "Security",
        title: "Nastav heslo i k účtu z Google loginu.",
        description: "Pro social-only účet je nastavení hesla další čistý krok v auth modulu, ne starý fallback formulář.",
        statLabel: "Security",
        statValue: "Set Password",
        statDescription: "Pokud už heslo existuje, backend vrátí redirect na změnu hesla.",
      };
    case "reauthenticate":
      return {
        eyebrow: "Security",
        title: "Potvrzení přístupu bez odskoku mimo auth modul.",
        description: "Když je potřeba znovu potvrdit citlivou akci, heslo se ověří ve stejném Vue auth flow.",
        statLabel: "Reauth",
        statValue: "Password Check",
        statDescription: "Po úspěchu se uživatel vrátí přesně tam, odkud přišel.",
      };
    case "logout":
      return {
        eyebrow: "Session",
        title: "Odhlášení bez zbytečného tření.",
        description: "Jedno potvrzení, jeden výsledek. Logout screen používá stejnou strukturu jako zbytek auth flow.",
        statLabel: "Action",
        statValue: "Logout",
        statDescription: "Po potvrzení tě vrátíme na přihlášení.",
      };
    case "inactive":
      return {
        eyebrow: "Account State",
        title: "Tento účet teď není aktivní.",
        description: "I fallback a chybové auth stavy drží stejnou kvalitu a tonality jako hlavní flow.",
        statLabel: "Fallback",
        statValue: "Inactive",
        statDescription: "Nabídneme další jasné kroky místo slepé uličky.",
      };
    case "social-error":
      return {
        eyebrow: "Social Login",
        title: "Google flow se tentokrát nepodařilo dokončit.",
        description: "Když externí provider selže, uživatel pořád zůstává v našem produktu a dostává srozumitelnou cestu dál.",
        statLabel: "Fallback",
        statValue: "Retry",
        statDescription: "Může zkusit Google znovu nebo přejít na e-mail a heslo.",
      };
    case "social-cancelled":
      return {
        eyebrow: "Social Login",
        title: "Přihlášení bylo zrušeno ještě před dokončením.",
        description: "Neutral state, žádná panika. Jen čistá možnost zkusit to znovu nebo přejít na registraci.",
        statLabel: "State",
        statValue: "Cancelled",
        statDescription: "Značka zůstává klidná i v nedokončeném flow.",
      };
    case "connections":
      return {
        eyebrow: "Connected Accounts",
        title: "Správa providerů bez vizuálního chaosu.",
        description: "Connections používají stejný shell, ale obsah je přehledový. Řádky providerů fungují jako čisté management karty.",
        statLabel: "Providers",
        statValue: "Google",
        statDescription: "Připojení i odpojení zůstávají oddělené akce a destruktivní CTA není primární.",
      };
    default:
      return {
        eyebrow: "Training Workspace",
        title: "Vrať se do plánu, ne do chaosu.",
        description: "Všechny měsíční plány, splněné aktivity i spolupráce se sportovci zůstávají v jednom čistém workspace.",
        statLabel: "This week",
        statValue: "18 / 22",
        statDescription: "Splněných jednotek napříč svěřenci. Auth působí jako vstup do stejného produktu, ne do cizího modulu.",
      };
  }
});

function clearErrors() {
  formError.value = "";
  fieldErrors.value = {};
}

function googleLoginUrl(process?: "connect") {
  return process ? `/accounts/google/login/?process=${process}` : "/accounts/google/login/";
}

function navigateTo(url: string) {
  window.location.href = url;
}

function currentEmailKey() {
  return typeof route.params.key === "string" ? route.params.key : "";
}

function currentResetKeyParts() {
  return {
    uidb36: typeof route.params.uidb36 === "string" ? route.params.uidb36 : "",
    key: typeof route.params.key === "string" ? route.params.key : "",
  };
}

function firstError(name: string) {
  return fieldErrors.value[name]?.[0] || "";
}

async function submitLogin() {
  isSubmitting.value = true;
  clearErrors();
  try {
    const response = await loginWithPassword({
      email: loginForm.email,
      password: loginForm.password,
      remember: loginForm.remember,
    });
    await authStore.refresh();
    navigateTo(response.redirect_to);
  } catch (error: unknown) {
    const maybeError = error as { response?: { data?: { message?: string; errors?: Record<string, string[]> } } };
    formError.value = maybeError.response?.data?.message || "Prihlaseni se nepodarilo.";
    fieldErrors.value = maybeError.response?.data?.errors || {};
  } finally {
    isSubmitting.value = false;
  }
}

async function submitSignup() {
  isSubmitting.value = true;
  clearErrors();
  try {
    const response = await signupWithPassword({
      first_name: signupForm.firstName,
      last_name: signupForm.lastName,
      email: signupForm.email,
      role: signupForm.role,
      password: signupForm.password,
      password_confirmation: signupForm.passwordConfirmation,
    });
    navigateTo(response.redirect_to);
  } catch (error: unknown) {
    const maybeError = error as { response?: { data?: { message?: string; errors?: Record<string, string[]> } } };
    formError.value = maybeError.response?.data?.message || "Registraci se nepodarilo dokoncit.";
    fieldErrors.value = maybeError.response?.data?.errors || {};
  } finally {
    isSubmitting.value = false;
  }
}

async function submitPasswordReset() {
  isSubmitting.value = true;
  clearErrors();
  try {
    const response = await requestPasswordReset(resetForm.email);
    await router.push(response.redirect_to);
  } catch (error: unknown) {
    const maybeError = error as { response?: { data?: { message?: string; errors?: Record<string, string[]> } } };
    formError.value = maybeError.response?.data?.message || "Obnovu hesla se nepodarilo zahajit.";
    fieldErrors.value = maybeError.response?.data?.errors || {};
  } finally {
    isSubmitting.value = false;
  }
}

async function submitLogout() {
  isSubmitting.value = true;
  clearErrors();
  try {
    const response = await logoutFromSession();
    authStore.user = null;
    navigateTo(response.redirect_to);
  } catch {
    formError.value = "Odhlaseni se nepodarilo dokoncit.";
  } finally {
    isSubmitting.value = false;
  }
}

async function loadEmailConfirmState() {
  const key = currentEmailKey();
  if (!key) return;

  emailConfirmState.value.isLoading = true;
  emailConfirmState.value.message = "";
  try {
    const response = await fetchEmailConfirmState(key);
    emailConfirmState.value.canConfirm = response.can_confirm;
    emailConfirmState.value.email = response.email || "";
    emailConfirmState.value.userDisplay = response.user?.display || "";
  } catch (error: unknown) {
    const maybeError = error as { response?: { data?: { message?: string } } };
    emailConfirmState.value.canConfirm = false;
    emailConfirmState.value.message = maybeError.response?.data?.message || "Tento potvrzovaci odkaz vyprsel nebo je neplatny.";
  } finally {
    emailConfirmState.value.isLoading = false;
  }
}

async function submitEmailConfirm() {
  const key = currentEmailKey();
  if (!key) return;

  isSubmitting.value = true;
  formError.value = "";
  try {
    const response = await confirmEmailKey(key);
    navigateTo(response.redirect_to);
  } catch (error: unknown) {
    const maybeError = error as { response?: { data?: { message?: string } } };
    formError.value = maybeError.response?.data?.message || "E-mail se nepodarilo potvrdit.";
  } finally {
    isSubmitting.value = false;
  }
}

async function loadPasswordResetKeyState() {
  const { uidb36, key } = currentResetKeyParts();
  if (!uidb36 || !key) return;

  passwordResetKeyState.value.isLoading = true;
  passwordResetKeyState.value.message = "";
  try {
    const response = await fetchPasswordResetKeyState(uidb36, key);
    if (response.redirect_to) {
      await router.replace(response.redirect_to);
      return;
    }
    passwordResetKeyState.value.tokenValid = response.token_valid;
    passwordResetKeyState.value.message = response.message || "";
  } catch (error: unknown) {
    const maybeError = error as { response?: { data?: { message?: string; token_valid?: boolean } } };
    passwordResetKeyState.value.tokenValid = false;
    passwordResetKeyState.value.message = maybeError.response?.data?.message || "Tento odkaz pro obnovu hesla uz neni platny.";
  } finally {
    passwordResetKeyState.value.isLoading = false;
  }
}

async function loadEmailAddresses() {
  emailManagementState.value.isLoading = true;
  try {
    const response = await fetchEmailAddresses();
    emailManagementState.value.canAddEmail = response.can_add_email;
    emailManagementState.value.emails = response.emails as typeof emailManagementState.value.emails;
  } catch {
    formError.value = "Nepodarilo se nacist e-mailove adresy.";
  } finally {
    emailManagementState.value.isLoading = false;
  }
}

async function runEmailAction(action: "add" | "primary" | "send" | "remove", payload: { email?: string; new_email?: string }) {
  isSubmitting.value = true;
  clearErrors();
  try {
    const response = await mutateEmailAddress(action, payload);
    if (response.redirect_to === "/accounts/confirm-email/") {
      await router.push(response.redirect_to);
      return;
    }
    await loadEmailAddresses();
  } catch (error: unknown) {
    const maybeError = error as { response?: { data?: { message?: string; errors?: Record<string, string[]> } } };
    formError.value = maybeError.response?.data?.message || "Akci nad e-mailem se nepodarilo dokoncit.";
    fieldErrors.value = maybeError.response?.data?.errors || {};
  } finally {
    isSubmitting.value = false;
  }
}

async function submitPasswordChange() {
  isSubmitting.value = true;
  clearErrors();
  try {
    const response = await changePassword(
      passwordChangeForm.currentPassword,
      passwordChangeForm.password,
      passwordChangeForm.passwordConfirmation,
    );
    navigateTo(response.redirect_to);
  } catch (error: unknown) {
    const maybeError = error as { response?: { data?: { message?: string; errors?: Record<string, string[]> } } };
    formError.value = maybeError.response?.data?.message || "Zmenu hesla se nepodarilo ulozit.";
    fieldErrors.value = maybeError.response?.data?.errors || {};
  } finally {
    isSubmitting.value = false;
  }
}

async function loadPasswordSetState() {
  passwordSetState.value.isLoading = true;
  try {
    const response = await fetchPasswordSetState();
    passwordSetState.value.hasUsablePassword = response.has_usable_password;
    if (response.redirect_to) {
      await router.replace(response.redirect_to);
    }
  } catch {
    formError.value = "Nepodarilo se nacist stav hesla.";
  } finally {
    passwordSetState.value.isLoading = false;
  }
}

async function loadSocialConnections() {
  socialConnectionsState.value.isLoading = true;
  try {
    const response = await fetchSocialConnections();
    socialConnectionsState.value.accounts = response.accounts as typeof socialConnectionsState.value.accounts;
    socialConnectionsState.value.connectGoogleUrl = response.connect_google_url;
  } catch {
    formError.value = "Nepodarilo se nacist propojene ucty.";
  } finally {
    socialConnectionsState.value.isLoading = false;
  }
}

async function submitDisconnectSocialAccount(accountId: number) {
  isSubmitting.value = true;
  clearErrors();
  try {
    await disconnectSocialAccount(accountId);
    await loadSocialConnections();
  } catch (error: unknown) {
    const maybeError = error as { response?: { data?: { message?: string } } };
    formError.value = maybeError.response?.data?.message || "Externi ucet se nepodarilo odpojit.";
  } finally {
    isSubmitting.value = false;
  }
}

async function loadReauthenticateState() {
  reauthenticateState.value.isLoading = true;
  try {
    const next = typeof route.query.next === "string" ? route.query.next : undefined;
    const response = await fetchReauthenticateState(next);
    reauthenticateState.value.next = response.next;
  } catch {
    formError.value = "Nepodarilo se nacist potvrzeni pristupu.";
  } finally {
    reauthenticateState.value.isLoading = false;
  }
}

async function submitReauthenticateAction() {
  isSubmitting.value = true;
  clearErrors();
  try {
    const response = await submitReauthenticate(reauthenticateForm.password, reauthenticateState.value.next);
    navigateTo(response.redirect_to);
  } catch (error: unknown) {
    const maybeError = error as { response?: { data?: { message?: string; errors?: Record<string, string[]> } } };
    formError.value = maybeError.response?.data?.message || "Potvrzeni pristupu se nepodarilo.";
    fieldErrors.value = maybeError.response?.data?.errors || {};
  } finally {
    isSubmitting.value = false;
  }
}

async function submitPasswordSet() {
  isSubmitting.value = true;
  clearErrors();
  try {
    const response = await setPassword(passwordSetForm.password, passwordSetForm.passwordConfirmation);
    navigateTo(response.redirect_to);
  } catch (error: unknown) {
    const maybeError = error as { response?: { data?: { message?: string; errors?: Record<string, string[]> } } };
    formError.value = maybeError.response?.data?.message || "Nastaveni hesla se nepodarilo ulozit.";
    fieldErrors.value = maybeError.response?.data?.errors || {};
  } finally {
    isSubmitting.value = false;
  }
}

async function submitResetKeyPassword() {
  const { uidb36, key } = currentResetKeyParts();
  if (!uidb36 || !key) return;

  isSubmitting.value = true;
  clearErrors();
  try {
    const response = await submitPasswordResetFromKey(uidb36, key, resetKeyForm.password, resetKeyForm.passwordConfirmation);
    await router.push(response.redirect_to);
  } catch (error: unknown) {
    const maybeError = error as { response?: { data?: { message?: string; errors?: Record<string, string[]> } } };
    formError.value = maybeError.response?.data?.message || "Zmenu hesla se nepodarilo dokoncit.";
    fieldErrors.value = maybeError.response?.data?.errors || {};
  } finally {
    isSubmitting.value = false;
  }
}

watch(
  () => route.fullPath,
  () => {
    if (screen.value === "email-confirm-key") {
      void loadEmailConfirmState();
    }
    if (screen.value === "password-reset-key") {
      void loadPasswordResetKeyState();
    }
    if (screen.value === "email-management") {
      void loadEmailAddresses();
    }
    if (screen.value === "password-set") {
      void loadPasswordSetState();
    }
    if (screen.value === "connections") {
      void loadSocialConnections();
    }
    if (screen.value === "reauthenticate") {
      void loadReauthenticateState();
    }
  },
  { immediate: true },
);
</script>

<template>
  <main class="auth-flow-page">
    <div class="auth-flow-page__wrap">
      <AuthPreviewShell
        :brand-eyebrow="shellConfig.eyebrow"
        :brand-title="shellConfig.title"
        :brand-description="shellConfig.description"
        :stat-label="shellConfig.statLabel"
        :stat-value="shellConfig.statValue"
        :stat-description="shellConfig.statDescription"
      >
        <div v-if="screen === 'login'" class="auth-flow-card">
          <div class="auth-flow-card__eyebrow">Authentication</div>
          <h1>Vítej zpět</h1>
          <p>Přihlas se a pokračuj do svého tréninkového přehledu, plánů a posledních importů.</p>

          <button class="auth-flow-button auth-flow-button--google" type="button" @click="navigateTo(googleLoginUrl())">
            <span class="auth-flow-google-badge">G</span>
            <span>Pokračovat přes Google</span>
          </button>

          <div class="auth-flow-divider">nebo</div>

          <label class="auth-flow-field">
            <span>E-mail</span>
            <input v-model="loginForm.email" type="email" autocomplete="email" />
            <small v-if="firstError('login')" class="is-danger">{{ firstError("login") }}</small>
          </label>

          <label class="auth-flow-field">
            <div class="auth-flow-inline">
              <span>Heslo</span>
              <RouterLink to="/accounts/password/reset/">Zapomenuté heslo?</RouterLink>
            </div>
            <input v-model="loginForm.password" type="password" autocomplete="current-password" />
            <small v-if="firstError('password')" class="is-danger">{{ firstError("password") }}</small>
          </label>

          <label class="auth-flow-check">
            <input v-model="loginForm.remember" type="checkbox" />
            <span>Zapamatovat si mě</span>
          </label>

          <p v-if="formError" class="auth-flow-error">{{ formError }}</p>

          <button class="auth-flow-button auth-flow-button--primary" type="button" :disabled="isSubmitting" @click="submitLogin">
            {{ isSubmitting ? "Prihlasuji..." : "Přihlásit se" }}
          </button>

          <div class="auth-flow-footer">
            Nemáš účet?
            <RouterLink to="/accounts/signup/">Registrovat se</RouterLink>
          </div>
        </div>

        <div v-else-if="screen === 'signup'" class="auth-flow-card">
          <div class="auth-flow-card__eyebrow">Authentication</div>
          <h1>Vytvoř si účet</h1>
          <p>Založ si EnduroBuddy účet a připrav prostor pro své tréninky nebo sportovce.</p>

          <button class="auth-flow-button auth-flow-button--google" type="button" @click="navigateTo(googleLoginUrl())">
            <span class="auth-flow-google-badge">G</span>
            <span>Pokračovat přes Google</span>
          </button>

          <div class="auth-flow-divider">nebo</div>

          <div class="auth-flow-grid">
            <label class="auth-flow-field">
              <span>Jméno</span>
              <input v-model="signupForm.firstName" type="text" autocomplete="given-name" />
              <small v-if="firstError('first_name')" class="is-danger">{{ firstError("first_name") }}</small>
            </label>

            <label class="auth-flow-field">
              <span>Příjmení</span>
              <input v-model="signupForm.lastName" type="text" autocomplete="family-name" />
              <small v-if="firstError('last_name')" class="is-danger">{{ firstError("last_name") }}</small>
            </label>
          </div>

          <label class="auth-flow-field">
            <span>E-mail</span>
            <input v-model="signupForm.email" type="email" autocomplete="email" />
            <small v-if="firstError('email')" class="is-danger">{{ firstError("email") }}</small>
          </label>

          <label class="auth-flow-field">
            <span>Role</span>
            <select v-model="signupForm.role">
              <option value="ATHLETE">Svěřenec</option>
              <option value="COACH">Trenér</option>
            </select>
            <small v-if="firstError('role')" class="is-danger">{{ firstError("role") }}</small>
          </label>

          <div class="auth-flow-grid">
            <label class="auth-flow-field">
              <span>Heslo</span>
              <input v-model="signupForm.password" type="password" autocomplete="new-password" />
              <small v-if="firstError('password1')" class="is-danger">{{ firstError("password1") }}</small>
            </label>

            <label class="auth-flow-field">
              <span>Heslo znovu</span>
              <input v-model="signupForm.passwordConfirmation" type="password" autocomplete="new-password" />
              <small v-if="firstError('password2')" class="is-danger">{{ firstError("password2") }}</small>
            </label>
          </div>

          <p v-if="formError" class="auth-flow-error">{{ formError }}</p>

          <button class="auth-flow-button auth-flow-button--primary" type="button" :disabled="isSubmitting" @click="submitSignup">
            {{ isSubmitting ? "Registruji..." : "Registrovat se" }}
          </button>

          <div class="auth-flow-footer">
            Už účet máš?
            <RouterLink to="/accounts/login/">Přihlásit se</RouterLink>
          </div>
        </div>

        <div v-else-if="screen === 'password-reset'" class="auth-flow-card">
          <div class="auth-flow-card__eyebrow">Password Reset</div>
          <h1>Obnovit heslo</h1>
          <p>Zadej e-mail k účtu a pošleme ti odkaz pro nastavení nového hesla.</p>

          <label class="auth-flow-field">
            <span>E-mail</span>
            <input v-model="resetForm.email" type="email" autocomplete="email" />
            <small v-if="firstError('email')" class="is-danger">{{ firstError("email") }}</small>
          </label>

          <p v-if="formError" class="auth-flow-error">{{ formError }}</p>

          <button class="auth-flow-button auth-flow-button--primary" type="button" :disabled="isSubmitting" @click="submitPasswordReset">
            {{ isSubmitting ? "Posilam..." : "Poslat obnovovací odkaz" }}
          </button>

          <div class="auth-flow-footer">
            <RouterLink to="/accounts/login/">Zpět na přihlášení</RouterLink>
          </div>
        </div>

        <div v-else-if="screen === 'password-reset-done'" class="auth-flow-card auth-flow-card--status">
          <span class="auth-flow-chip">Email sent</span>
          <h1>Zkontroluj e-mail</h1>
          <p>Pokud účet s tímto e-mailem existuje, poslali jsme odkaz pro obnovu hesla.</p>
          <RouterLink class="auth-flow-button auth-flow-button--primary" to="/accounts/login/">Zpět na přihlášení</RouterLink>
        </div>

        <div v-else-if="screen === 'password-reset-key'" class="auth-flow-card">
          <div v-if="passwordResetKeyState.isLoading" class="auth-flow-loading">
            Ověřuji odkaz pro obnovu hesla...
          </div>

          <template v-else-if="!passwordResetKeyState.tokenValid">
            <span class="auth-flow-chip auth-flow-chip--danger">Invalid link</span>
            <h1>Neplatný odkaz</h1>
            <p>{{ passwordResetKeyState.message || "Tento odkaz pro obnovu hesla uz neni platny." }}</p>
            <RouterLink class="auth-flow-button auth-flow-button--primary" to="/accounts/password/reset/">Vyžádat nový odkaz</RouterLink>
          </template>

          <template v-else>
            <div class="auth-flow-card__eyebrow">Password Reset</div>
            <h1>Nastav nové heslo</h1>
            <p>Zvol silné heslo pro svůj účet EnduroBuddy.</p>

            <label class="auth-flow-field">
              <span>Nové heslo</span>
              <input v-model="resetKeyForm.password" type="password" autocomplete="new-password" />
              <small v-if="firstError('password1')" class="is-danger">{{ firstError("password1") }}</small>
            </label>

            <label class="auth-flow-field">
              <span>Heslo znovu</span>
              <input v-model="resetKeyForm.passwordConfirmation" type="password" autocomplete="new-password" />
              <small v-if="firstError('password2')" class="is-danger">{{ firstError("password2") }}</small>
            </label>

            <p v-if="formError" class="auth-flow-error">{{ formError }}</p>

            <button class="auth-flow-button auth-flow-button--primary" type="button" :disabled="isSubmitting" @click="submitResetKeyPassword">
              {{ isSubmitting ? "Ukladam..." : "Změnit heslo" }}
            </button>
            <RouterLink class="auth-flow-button auth-flow-button--secondary" to="/accounts/login/">Zpět na přihlášení</RouterLink>
          </template>
        </div>

        <div v-else-if="screen === 'password-reset-key-done'" class="auth-flow-card auth-flow-card--status">
          <span class="auth-flow-chip">Password updated</span>
          <h1>Heslo bylo změněno</h1>
          <p>Tvé heslo bylo úspěšně změněno.</p>
          <RouterLink class="auth-flow-button auth-flow-button--primary" to="/accounts/login/">Přihlásit se</RouterLink>
        </div>

        <div v-else-if="screen === 'verification-sent'" class="auth-flow-card auth-flow-card--status">
          <span class="auth-flow-chip auth-flow-chip--blue">Verification sent</span>
          <h1>Ověř svou e-mailovou adresu</h1>
          <p>Poslali jsme ti ověřovací e-mail. Dokonči registraci kliknutím na odkaz v e-mailu. Pokud zprávu nevidíš, zkontroluj i spam.</p>
          <RouterLink class="auth-flow-button auth-flow-button--primary" to="/accounts/login/">Zpět na přihlášení</RouterLink>
        </div>

        <div v-else-if="screen === 'email-confirm-key'" class="auth-flow-card auth-flow-card--status">
          <div v-if="emailConfirmState.isLoading" class="auth-flow-loading">
            Ověřuji potvrzovací odkaz...
          </div>

          <template v-else-if="!emailConfirmState.canConfirm">
            <span class="auth-flow-chip auth-flow-chip--danger">Invalid link</span>
            <h1>Potvrzení e-mailu</h1>
            <p>{{ emailConfirmState.message || "Tento potvrzovaci odkaz vyprsel nebo je neplatny." }}</p>
            <RouterLink class="auth-flow-button auth-flow-button--primary" to="/accounts/confirm-email/">Vyžádat nové potvrzení</RouterLink>
          </template>

          <template v-else>
            <span class="auth-flow-chip auth-flow-chip--blue">Confirm email</span>
            <h1>Potvrzení e-mailu</h1>
            <p>
              Potvrď, že <strong>{{ emailConfirmState.email }}</strong> je e-mailová adresa uživatele
              {{ emailConfirmState.userDisplay }}.
            </p>
            <p v-if="formError" class="auth-flow-error">{{ formError }}</p>
            <button class="auth-flow-button auth-flow-button--primary" type="button" :disabled="isSubmitting" @click="submitEmailConfirm">
              {{ isSubmitting ? "Potvrzuji..." : "Potvrdit" }}
            </button>
            <RouterLink class="auth-flow-button auth-flow-button--secondary" to="/accounts/login/">Zpět na přihlášení</RouterLink>
          </template>
        </div>

        <div v-else-if="screen === 'email-management'" class="auth-flow-card">
          <div class="auth-flow-card__eyebrow">Email Management</div>
          <h1>E-mailové adresy</h1>
          <p>Správa adres přiřazených k účtu.</p>

          <div v-if="emailManagementState.isLoading" class="auth-flow-loading">Načítám e-mailové adresy...</div>

          <template v-else>
            <article v-for="emailItem in emailManagementState.emails" :key="emailItem.email" class="auth-connection-row">
              <div class="auth-connection-row__logo">@</div>
              <div class="auth-connection-row__content">
                <strong>{{ emailItem.email }}</strong>
                <span>
                  {{ emailItem.primary ? "Primární" : "Sekundární" }} ·
                  {{ emailItem.verified ? "Ověřený" : "Neověřený" }}
                </span>
              </div>
              <div class="auth-connection-actions">
                <button
                  v-if="emailItem.can_mark_primary && !emailItem.primary"
                  class="auth-flow-button auth-flow-button--secondary auth-flow-button--compact"
                  type="button"
                  @click="runEmailAction('primary', { email: emailItem.email })"
                >
                  Nastavit jako primární
                </button>
                <button
                  v-if="!emailItem.verified"
                  class="auth-flow-button auth-flow-button--secondary auth-flow-button--compact"
                  type="button"
                  @click="runEmailAction('send', { email: emailItem.email })"
                >
                  Poslat ověření znovu
                </button>
                <button
                  v-if="emailItem.can_delete"
                  class="auth-flow-button auth-flow-button--secondary auth-flow-button--compact"
                  type="button"
                  @click="runEmailAction('remove', { email: emailItem.email })"
                >
                  Odebrat
                </button>
              </div>
            </article>

            <label v-if="emailManagementState.canAddEmail" class="auth-flow-field">
              <span>Přidat e-mailovou adresu</span>
              <input v-model="emailAddForm.newEmail" type="email" autocomplete="email" />
              <small v-if="firstError('email')" class="is-danger">{{ firstError("email") }}</small>
            </label>

            <p v-if="formError" class="auth-flow-error">{{ formError }}</p>

            <button
              v-if="emailManagementState.canAddEmail"
              class="auth-flow-button auth-flow-button--primary"
              type="button"
              :disabled="isSubmitting"
              @click="runEmailAction('add', { new_email: emailAddForm.newEmail })"
            >
              Přidat e-mail
            </button>
          </template>
        </div>

        <div v-else-if="screen === 'password-change'" class="auth-flow-card">
          <div class="auth-flow-card__eyebrow">Security</div>
          <h1>Změna hesla</h1>
          <p>Změň heslo bez opuštění nového auth flow.</p>

          <label class="auth-flow-field">
            <span>Současné heslo</span>
            <input v-model="passwordChangeForm.currentPassword" type="password" autocomplete="current-password" />
            <small v-if="firstError('oldpassword')" class="is-danger">{{ firstError("oldpassword") }}</small>
          </label>

          <label class="auth-flow-field">
            <span>Nové heslo</span>
            <input v-model="passwordChangeForm.password" type="password" autocomplete="new-password" />
            <small v-if="firstError('password1')" class="is-danger">{{ firstError("password1") }}</small>
          </label>

          <label class="auth-flow-field">
            <span>Nové heslo znovu</span>
            <input v-model="passwordChangeForm.passwordConfirmation" type="password" autocomplete="new-password" />
            <small v-if="firstError('password2')" class="is-danger">{{ firstError("password2") }}</small>
          </label>

          <p v-if="formError" class="auth-flow-error">{{ formError }}</p>

          <button class="auth-flow-button auth-flow-button--primary" type="button" :disabled="isSubmitting" @click="submitPasswordChange">
            {{ isSubmitting ? "Ukladam..." : "Uložit nové heslo" }}
          </button>

          <RouterLink class="auth-flow-button auth-flow-button--secondary" to="/accounts/password/reset/">Zapomenuté heslo?</RouterLink>
        </div>

        <div v-else-if="screen === 'password-set'" class="auth-flow-card">
          <div v-if="passwordSetState.isLoading" class="auth-flow-loading">Načítám stav hesla...</div>

          <template v-else>
            <div class="auth-flow-card__eyebrow">Security</div>
            <h1>Nastavit heslo</h1>
            <p>Použij tuhle stránku, když má účet přihlášení přes externího poskytovatele a chceš si nastavit i klasické heslo.</p>

            <label class="auth-flow-field">
              <span>Nové heslo</span>
              <input v-model="passwordSetForm.password" type="password" autocomplete="new-password" />
              <small v-if="firstError('password1')" class="is-danger">{{ firstError("password1") }}</small>
            </label>

            <label class="auth-flow-field">
              <span>Nové heslo znovu</span>
              <input v-model="passwordSetForm.passwordConfirmation" type="password" autocomplete="new-password" />
              <small v-if="firstError('password2')" class="is-danger">{{ firstError("password2") }}</small>
            </label>

            <p v-if="formError" class="auth-flow-error">{{ formError }}</p>

            <button class="auth-flow-button auth-flow-button--primary" type="button" :disabled="isSubmitting" @click="submitPasswordSet">
              {{ isSubmitting ? "Ukladam..." : "Nastavit heslo" }}
            </button>
          </template>
        </div>

        <div v-else-if="screen === 'logout'" class="auth-flow-card auth-flow-card--status">
          <span class="auth-flow-chip">Session</span>
          <h1>Opravdu se chceš odhlásit?</h1>
          <p>Po potvrzení tě vrátíme na přihlášení.</p>
          <p v-if="formError" class="auth-flow-error">{{ formError }}</p>
          <button class="auth-flow-button auth-flow-button--primary" type="button" :disabled="isSubmitting" @click="submitLogout">
            {{ isSubmitting ? "Odhlasuji..." : "Odhlásit se" }}
          </button>
          <RouterLink class="auth-flow-button auth-flow-button--secondary" to="/app/dashboard">Zpět</RouterLink>
        </div>

        <div v-else-if="screen === 'inactive'" class="auth-flow-card auth-flow-card--status">
          <span class="auth-flow-chip auth-flow-chip--danger">Inactive</span>
          <h1>Účet není aktivní</h1>
          <p>K tomuto účtu se teď nejde přihlásit. Zkus obnovu hesla nebo kontaktuj support.</p>
          <RouterLink class="auth-flow-button auth-flow-button--primary" to="/accounts/login/">Zpět na přihlášení</RouterLink>
          <RouterLink class="auth-flow-button auth-flow-button--secondary" to="/accounts/password/reset/">Obnovit heslo</RouterLink>
        </div>

        <div v-else-if="screen === 'social-error'" class="auth-flow-card auth-flow-card--status">
          <span class="auth-flow-chip auth-flow-chip--danger">Error</span>
          <h1>Přihlášení přes poskytovatele se nezdařilo</h1>
          <p>Při přihlášení přes Google nebo jiný externí účet nastala chyba. Zkus to prosím znovu.</p>
          <button class="auth-flow-button auth-flow-button--primary" type="button" @click="navigateTo(googleLoginUrl())">Zkusit znovu</button>
          <RouterLink class="auth-flow-button auth-flow-button--secondary" to="/accounts/login/">Použít e-mail</RouterLink>
        </div>

        <div v-else-if="screen === 'social-cancelled'" class="auth-flow-card auth-flow-card--status">
          <span class="auth-flow-chip auth-flow-chip--blue">Cancelled</span>
          <h1>Přihlášení bylo zrušeno</h1>
          <p>Přihlášení přes externí účet bylo přerušeno ještě před dokončením. Můžeš to zkusit znovu.</p>
          <button class="auth-flow-button auth-flow-button--primary" type="button" @click="navigateTo(googleLoginUrl())">Zkusit znovu</button>
          <RouterLink class="auth-flow-button auth-flow-button--secondary" to="/accounts/signup/">Registrace</RouterLink>
        </div>

        <div v-else-if="screen === 'connections'" class="auth-flow-card">
          <div class="auth-flow-card__eyebrow">Connections</div>
          <h1>Propojené účty</h1>
          <p>Spravuj, které externí účty můžeš použít pro přihlášení do EnduroBuddy.</p>

          <div v-if="socialConnectionsState.isLoading" class="auth-flow-loading">Načítám propojené účty...</div>

          <article v-for="account in socialConnectionsState.accounts" v-else :key="account.id" class="auth-connection-row">
            <div class="auth-connection-row__logo">{{ account.brand_name.slice(0, 1) }}</div>
            <div class="auth-connection-row__content">
              <strong>{{ account.provider_name }}</strong>
              <span>{{ account.label }}</span>
            </div>
            <div class="auth-connection-actions">
              <button class="auth-flow-button auth-flow-button--secondary auth-flow-button--compact" type="button" :disabled="isSubmitting" @click="submitDisconnectSocialAccount(account.id)">
                Odpojit
              </button>
            </div>
          </article>

          <p v-if="!socialConnectionsState.isLoading && !socialConnectionsState.accounts.length" class="auth-flow-empty">
            K tomuto účtu zatím není připojený žádný externí poskytovatel.
          </p>

          <p v-if="formError" class="auth-flow-error">{{ formError }}</p>

          <button class="auth-flow-button auth-flow-button--primary" type="button" @click="navigateTo(socialConnectionsState.connectGoogleUrl)">
            Připojit Google účet
          </button>
          <RouterLink class="auth-flow-button auth-flow-button--secondary" to="/app/dashboard">Zpět do aplikace</RouterLink>
        </div>

        <div v-else-if="screen === 'reauthenticate'" class="auth-flow-card">
          <div v-if="reauthenticateState.isLoading" class="auth-flow-loading">Načítám potvrzení přístupu...</div>

          <template v-else>
            <div class="auth-flow-card__eyebrow">Security</div>
            <h1>Potvrzení přístupu</h1>
            <p>Pro pokračování potvrď své heslo.</p>

            <label class="auth-flow-field">
              <span>Heslo</span>
              <input v-model="reauthenticateForm.password" type="password" autocomplete="current-password" />
              <small v-if="firstError('password')" class="is-danger">{{ firstError("password") }}</small>
            </label>

            <p v-if="formError" class="auth-flow-error">{{ formError }}</p>

            <button class="auth-flow-button auth-flow-button--primary" type="button" :disabled="isSubmitting" @click="submitReauthenticateAction">
              {{ isSubmitting ? "Potvrzuji..." : "Potvrdit" }}
            </button>
          </template>
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

.auth-flow-card--status {
  align-content: start;
}

.auth-flow-card__eyebrow,
.auth-flow-field span,
.auth-flow-chip {
  color: var(--eb-text-muted);
  font-size: var(--eb-type-label-size);
  font-weight: 700;
  letter-spacing: var(--eb-type-label-tracking);
  text-transform: uppercase;
}

.auth-flow-card h1 {
  margin: 0;
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-h1-size);
  font-weight: var(--eb-type-h1-weight);
  line-height: var(--eb-type-h1-line);
  letter-spacing: var(--eb-type-h1-tracking);
}

.auth-flow-card p,
.auth-flow-footer,
.auth-connection-row__content span {
  margin: 0;
  color: var(--eb-text-soft);
  font-size: var(--eb-type-body-size);
  line-height: var(--eb-type-body-line);
}

.auth-flow-button,
.auth-flow-field input,
.auth-flow-field select {
  min-height: 3rem;
  border-radius: 0.7rem;
}

.auth-flow-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.65rem;
  width: 100%;
  padding: 0 1rem;
  border: 1px solid transparent;
  font-size: var(--eb-type-small-size);
  font-weight: 700;
  letter-spacing: 0.02em;
  transition:
    transform 160ms ease,
    background 160ms ease,
    border-color 160ms ease;
}

.auth-flow-button:hover {
  transform: translateY(-1px);
}

.auth-flow-button--primary {
  background: var(--eb-lime);
  color: #09090b;
  box-shadow: var(--eb-glow-lime);
}

.auth-flow-button--secondary {
  border-color: var(--eb-border);
  background: transparent;
  color: var(--eb-text);
}

.auth-flow-button--google {
  justify-content: flex-start;
  border-color: var(--eb-border);
  background: var(--eb-surface);
  color: var(--eb-text);
}

.auth-flow-button--google:hover {
  transform: translateY(-1px);
  border-color: rgba(255, 255, 255, 0.18);
  background: var(--eb-surface-hover);
}

.auth-flow-google-badge {
  display: grid;
  place-items: center;
  width: 1.4rem;
  height: 1.4rem;
  border-radius: 999px;
  background: #fff;
  color: #4285f4;
  font-size: 0.85rem;
  font-weight: 700;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.auth-flow-divider {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 0.75rem;
  color: var(--eb-text-muted);
  font-size: var(--eb-type-label-size);
  font-weight: 700;
  letter-spacing: var(--eb-type-label-tracking);
  text-transform: uppercase;
}

.auth-flow-divider::before,
.auth-flow-divider::after {
  content: "";
  height: 1px;
  background: var(--eb-border);
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

.auth-flow-field input,
.auth-flow-field select {
  width: 100%;
  border: 1px solid var(--eb-border);
  padding: 0.8rem 0.9rem;
  background: #09090b;
  color: var(--eb-text);
}

.auth-flow-field input:focus,
.auth-flow-field select:focus {
  outline: none;
  border-color: rgba(200, 255, 0, 0.36);
  box-shadow: var(--eb-glow-lime);
}

.auth-flow-field small {
  color: var(--eb-text-muted);
  font-size: var(--eb-type-small-size);
}

.auth-flow-field small.is-danger,
.auth-flow-error {
  color: #fda4af;
}

.auth-flow-loading {
  color: var(--eb-text-soft);
  font-size: var(--eb-type-body-size);
}

.auth-flow-inline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.auth-flow-inline a,
.auth-flow-footer a {
  color: var(--eb-lime);
  font-weight: 600;
}

.auth-flow-check {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  color: var(--eb-text-soft);
  font-size: var(--eb-type-small-size);
}

.auth-flow-footer {
  text-align: center;
  font-size: var(--eb-type-small-size);
}

.auth-flow-chip {
  display: inline-flex;
  width: fit-content;
  padding: 0.42rem 0.55rem;
  border: 1px solid rgba(200, 255, 0, 0.2);
  border-radius: 999px;
  background: rgba(200, 255, 0, 0.1);
  color: var(--eb-lime);
}

.auth-flow-chip--blue {
  border-color: rgba(56, 189, 248, 0.2);
  background: rgba(56, 189, 248, 0.1);
  color: var(--eb-blue);
}

.auth-flow-chip--danger {
  border-color: rgba(244, 63, 94, 0.22);
  background: rgba(244, 63, 94, 0.1);
  color: #fda4af;
}

.auth-connection-row {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.75rem;
  align-items: center;
  padding: 0.95rem;
  border: 1px solid var(--eb-border);
  border-radius: 1rem;
  background: rgba(9, 9, 11, 0.5);
}

.auth-connection-row__logo {
  display: grid;
  place-items: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.85rem;
  background: #fff;
  color: #4285f4;
  font-size: 1rem;
  font-weight: 700;
}

.auth-connection-row__content {
  display: grid;
  gap: 0.2rem;
}

.auth-connection-row__content strong {
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-h3-size);
  font-weight: 600;
  letter-spacing: var(--eb-type-h3-tracking);
}

.auth-connection-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.auth-flow-button--compact {
  width: auto;
  min-height: 2.35rem;
  font-size: var(--eb-type-small-size);
  padding-inline: 0.85rem;
}

@media (max-width: 720px) {
  .auth-flow-page {
    padding-inline: 0.75rem;
  }

  .auth-flow-grid {
    grid-template-columns: 1fr;
  }

  .auth-connection-actions {
    flex-direction: column;
  }
}
</style>
