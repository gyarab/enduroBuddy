<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import AuthPreviewShell from "@/components/auth/AuthPreviewShell.vue";

type ScreenId =
  | "login"
  | "signup"
  | "google"
  | "google-signup"
  | "complete-profile"
  | "password-reset"
  | "status"
  | "connections"
  | "utility";

type ScreenNavItem = {
  id: ScreenId;
  label: string;
  note: string;
};

const route = useRoute();
const router = useRouter();

const screens: ScreenNavItem[] = [
  { id: "login", label: "Login", note: "Credential login + Google CTA" },
  { id: "signup", label: "Sign up", note: "Role-aware registration" },
  { id: "google", label: "Google continue", note: "Provider confirmation step" },
  { id: "google-signup", label: "Google completion", note: "Imported identity completion" },
  { id: "complete-profile", label: "Complete profile", note: "Onboarding role confirmation" },
  { id: "password-reset", label: "Password reset", note: "Recovery request state" },
  { id: "status", label: "Status pages", note: "Verification, done, error states" },
  { id: "connections", label: "Connections", note: "Linked providers management" },
  { id: "utility", label: "Utility states", note: "Logout, inactive, ratelimit" },
];

const currentScreenId = computed<ScreenId>(() => {
  const candidate = route.params.screen;
  const value = typeof candidate === "string" ? candidate : "login";
  return screens.some((screen) => screen.id === value) ? (value as ScreenId) : "login";
});

const currentScreen = computed(() => screens.find((screen) => screen.id === currentScreenId.value) ?? screens[0]);

function goToScreen(screenId: ScreenId) {
  void router.push({ name: "auth-preview", params: { screen: screenId } });
}
</script>

<template>
  <main class="auth-preview-page">
    <section class="auth-preview-page__hero">
      <div class="auth-preview-page__eyebrow">Vue Auth Frontend</div>
      <h1>Auth flow implementovaný ve Vue + TypeScript design systému.</h1>
      <p>
        Tohle je frontend auth modul připravený jako základ pro budoucí napojení na produkční login/signup API a Google redirect flow.
        Všechny hlavní obrazovky jsou sjednocené v jednom reusable shellu mimo app top nav.
      </p>
    </section>

    <section class="auth-preview-page__body">
      <aside class="auth-preview-nav">
        <div class="auth-preview-nav__head">
          <div class="auth-preview-page__eyebrow">Screens</div>
          <strong>{{ currentScreen.label }}</strong>
          <span>{{ currentScreen.note }}</span>
        </div>

        <div class="auth-preview-nav__list">
          <button
            v-for="screen in screens"
            :key="screen.id"
            class="auth-preview-nav__item"
            :class="{ 'is-active': screen.id === currentScreenId }"
            type="button"
            @click="goToScreen(screen.id)"
          >
            <span>{{ screen.label }}</span>
            <small>{{ screen.note }}</small>
          </button>
        </div>
      </aside>

      <div class="auth-preview-stage">
        <AuthPreviewShell
          v-if="currentScreenId === 'login'"
          brand-eyebrow="Training Workspace"
          brand-title="Vrať se do plánu, ne do chaosu."
          brand-description="Všechny měsíční plány, splněné aktivity i spolupráce se sportovci zůstávají v jednom čistém workspace."
          stat-label="Tento týden"
          stat-value="18 / 22"
          stat-description="Splněných jednotek napříč svěřenci. Auth působí jako vstup do stejného produktu, ne do cizího modulu."
        >
          <div class="auth-card">
            <div class="auth-card__eyebrow">Authentication</div>
            <h2>Vítej zpět</h2>
            <p>Přihlas se a pokračuj do svého tréninkového přehledu, plánů a posledních importů.</p>

            <button class="auth-button auth-button--google" type="button">
              <span class="auth-google-badge">G</span>
              <span>Pokračovat přes Google</span>
            </button>

            <div class="auth-divider">nebo</div>

            <label class="auth-field">
              <span>Uživatelské jméno nebo e-mail</span>
              <input value="vojta@endurobuddy.app" readonly />
            </label>

            <label class="auth-field">
              <div class="auth-inline">
                <span>Heslo</span>
                <a href="/accounts/password/reset/">Zapomenuté heslo?</a>
              </div>
              <input value="••••••••••••" readonly />
            </label>

            <label class="auth-check">
              <span class="auth-check__box">✓</span>
              <span>Zapamatovat si mě</span>
            </label>

            <button class="auth-button auth-button--primary" type="button">Přihlásit se</button>

            <div class="auth-footer">
              Nemáš účet?
              <button type="button" @click="goToScreen('signup')">Registrovat se</button>
            </div>
          </div>
        </AuthPreviewShell>

        <AuthPreviewShell
          v-else-if="currentScreenId === 'signup'"
          brand-eyebrow="Start Clean"
          brand-title="Začni plánovat s přesností od prvního dne."
          brand-description="Registrace je rychlá a už během prvního kroku je jasné, jestli vstupuješ jako coach nebo athlete."
          stat-label="Fast path"
          stat-value="Google First"
          stat-description="Social signup je preferovaný vstup, role a heslo mají jasné místo bez vizuálního šumu."
        >
          <div class="auth-card">
            <div class="auth-card__eyebrow">Authentication</div>
            <h2>Vytvoř si účet</h2>
            <p>Založ si EnduroBuddy účet a připrav prostor pro své tréninky nebo sportovce.</p>

            <button class="auth-button auth-button--google" type="button">
              <span class="auth-google-badge">G</span>
              <span>Pokračovat přes Google</span>
            </button>

            <div class="auth-divider">nebo</div>

            <div class="auth-grid">
              <label class="auth-field">
                <span>Jméno</span>
                <input value="Vojta" readonly />
              </label>

              <label class="auth-field">
                <span>Příjmení</span>
                <input value="Novák" readonly />
              </label>
            </div>

            <label class="auth-field">
              <span>E-mail</span>
              <input value="vojta@endurobuddy.app" readonly />
            </label>

            <label class="auth-field">
              <span>Role</span>
              <select disabled>
                <option>Coach</option>
              </select>
            </label>

            <div class="auth-grid">
              <label class="auth-field">
                <span>Heslo</span>
                <input value="••••••••••••" readonly />
              </label>

              <label class="auth-field">
                <span>Heslo znovu</span>
                <input value="••••••••••••" readonly />
              </label>
            </div>

            <button class="auth-button auth-button--primary" type="button">Registrovat se</button>

            <div class="auth-footer">
              Už účet máš?
              <button type="button" @click="goToScreen('login')">Přihlásit se</button>
            </div>
          </div>
        </AuthPreviewShell>

        <AuthPreviewShell
          v-else-if="currentScreenId === 'google'"
          brand-eyebrow="Google Flow"
          brand-title="Rychlý vstup bez ztráty kontextu."
          brand-description="Potvrzovací krok je klidný, stručný a říká přesně, co bude následovat po přesměrování na Google."
          stat-label="Provider"
          stat-value="Google"
          stat-description="Jeden potvrzovací krok před redirectem zvyšuje jistotu a snižuje drop-off."
        >
          <div class="auth-card">
            <div class="auth-card__eyebrow">Google Flow</div>
            <h2>Pokračovat přes Google</h2>
            <p>Chystáš se přihlásit pomocí Google účtu. Pokud účet ještě neexistuje, navážeme na registraci.</p>

            <div class="auth-status auth-status--blue">
              <div class="auth-status__icon">G</div>
              <div>
                <strong>Bezpečné přesměrování na Google</strong>
                <p>Po potvrzení se otevře Google login a po návratu tě vrátíme zpět do EnduroBuddy.</p>
              </div>
            </div>

            <button class="auth-button auth-button--primary" type="button">Pokračovat přes Google</button>
            <button class="auth-button auth-button--secondary" type="button" @click="goToScreen('login')">Zpět na přihlášení</button>
          </div>
        </AuthPreviewShell>

        <AuthPreviewShell
          v-else-if="currentScreenId === 'google-signup'"
          brand-eyebrow="Imported Identity"
          brand-title="Google dodá základ, my jen doplníme zbytek."
          brand-description="Předvyplněné údaje se odliší jako importované a uživatel přesně ví, co ještě potřebuje potvrdit."
          stat-label="Imported"
          stat-value="Name + Email"
          stat-description="Chybějící role je jediný povinný krok. Zbytek působí jako potvrzení, ne druhá registrace."
        >
          <div class="auth-card">
            <div class="auth-card__eyebrow">Google Flow</div>
            <h2>Dokonči svůj účet</h2>
            <p>Údaje z Google jsme načetli. Zkontroluj je a doplň, co chybí, abychom tě mohli pustit dál.</p>

            <div class="auth-grid">
              <label class="auth-field">
                <span>Jméno</span>
                <input class="is-imported" value="Vojta" readonly />
                <small>Načteno z Google profilu</small>
              </label>

              <label class="auth-field">
                <span>Příjmení</span>
                <input class="is-imported" value="Novák" readonly />
                <small>Načteno z Google profilu</small>
              </label>
            </div>

            <label class="auth-field">
              <span>E-mail</span>
              <input class="is-imported" value="vojta@gmail.com" readonly />
            </label>

            <label class="auth-field">
              <span>Role</span>
              <select disabled>
                <option>Vyber roli</option>
              </select>
              <small class="is-danger">Vyber prosím, jestli vstupuješ jako coach nebo athlete.</small>
            </label>

            <button class="auth-button auth-button--primary" type="button">Dokončit registraci</button>
            <button class="auth-button auth-button--ghost" type="button" @click="goToScreen('login')">Zpět na přihlášení</button>
          </div>
        </AuthPreviewShell>

        <AuthPreviewShell
          v-else-if="currentScreenId === 'complete-profile'"
          brand-eyebrow="Onboarding Step"
          brand-title="Doplň roli a můžeš pokračovat."
          brand-description="Incomplete profile používá stejný shell, jen se obsah mění na decision screen s vysvětlením obou rolí."
          stat-label="Decision"
          stat-value="Coach vs Athlete"
          stat-description="Role explainer zůstává v brand panelu a hlavní karta se drží jednoho úkolu."
        >
          <template #brand-extra>
            <div class="auth-role-grid">
              <article class="auth-role-card auth-role-card--lime">
                <strong>Coach</strong>
                <p>Plánuje pro více sportovců, organizuje skupiny a sleduje plnění.</p>
              </article>
              <article class="auth-role-card auth-role-card--blue">
                <strong>Athlete</strong>
                <p>Vidí svůj plán, zapisuje realitu a importuje aktivity.</p>
              </article>
            </div>
          </template>

          <div class="auth-card">
            <div class="auth-card__eyebrow">Profile Completion</div>
            <h2>Doplň svůj profil</h2>
            <p>Než tě pustíme do aplikace, potřebujeme potvrdit základní identitu a roli.</p>

            <div class="auth-grid">
              <label class="auth-field">
                <span>Jméno</span>
                <input value="Vojta" readonly />
              </label>

              <label class="auth-field">
                <span>Příjmení</span>
                <input value="Novák" readonly />
              </label>
            </div>

            <label class="auth-field">
              <span>Role</span>
              <select disabled>
                <option>Coach</option>
              </select>
            </label>

            <button class="auth-button auth-button--primary" type="button">Pokračovat</button>
            <button class="auth-button auth-button--secondary" type="button">Odhlásit se</button>
          </div>
        </AuthPreviewShell>

        <AuthPreviewShell
          v-else-if="currentScreenId === 'password-reset'"
          brand-eyebrow="Recovery"
          brand-title="Vrátíme tě zpět bez tření."
          brand-description="Recovery stránky jsou méně marketingové a víc utilitární. Jedna úloha, jedna akce, jeden klidný výsledek."
          stat-label="Secure Reset"
          stat-value="Email Link"
          stat-description="Support copy vysvětluje, že obnovovací odkaz pošleme jen pokud účet pro daný e-mail existuje."
        >
          <div class="auth-card">
            <div class="auth-card__eyebrow">Password Reset</div>
            <h2>Obnovit heslo</h2>
            <p>Zadej e-mail k účtu a pošleme ti odkaz pro nastavení nového hesla.</p>

            <label class="auth-field">
              <span>E-mail</span>
              <input value="vojta@endurobuddy.app" readonly />
            </label>

            <button class="auth-button auth-button--primary" type="button">Poslat obnovovací odkaz</button>
            <button class="auth-button auth-button--ghost" type="button" @click="goToScreen('login')">Zpět na přihlášení</button>
          </div>
        </AuthPreviewShell>

        <AuthPreviewShell
          v-else-if="currentScreenId === 'status'"
          brand-eyebrow="System States"
          brand-title="Všechny mezistavy mají stejný hlas i strukturu."
          brand-description="Úspěch, čekání i chyba používají stejnou status-page variantu shellu. Mění se jen chip, headline a sada CTA."
          stat-label="Coverage"
          stat-value="3 statusy"
          stat-description="Password reset done, verification sent i auth error drží stejnou komponentovou logiku."
        >
          <div class="auth-card auth-card--stacked">
            <div class="auth-status">
              <div class="auth-status__icon">✓</div>
              <div>
                <div class="auth-chip">Password updated</div>
                <strong>Heslo je změněné</strong>
                <p>Můžeš se znovu přihlásit a pokračovat tam, kde jsi skončil.</p>
              </div>
            </div>

            <div class="auth-status auth-status--blue">
              <div class="auth-status__icon">@</div>
              <div>
                <div class="auth-chip auth-chip--blue">Verification sent</div>
                <strong>Zkontroluj svou schránku</strong>
                <p>Ověřovací e-mail jsme právě poslali na `vojta@endurobuddy.app`.</p>
              </div>
            </div>

            <div class="auth-status auth-status--danger">
              <div class="auth-status__icon">!</div>
              <div>
                <div class="auth-chip auth-chip--danger">Error</div>
                <strong>Google přihlášení se nepodařilo dokončit</strong>
                <p>Zkus to znovu nebo pokračuj klasicky přes e-mail a heslo.</p>
              </div>
            </div>

            <div class="auth-grid auth-grid--actions">
              <button class="auth-button auth-button--primary" type="button">Zkusit znovu</button>
              <button class="auth-button auth-button--secondary" type="button">Použít e-mail</button>
            </div>
          </div>
        </AuthPreviewShell>

        <AuthPreviewShell
          v-else-if="currentScreenId === 'connections'"
          brand-eyebrow="Connected Accounts"
          brand-title="Správa providerů bez vizuálního chaosu."
          brand-description="Connections používají stejný shell, ale obsah je přehledový. Řádky providerů fungují jako čisté management karty."
          stat-label="Providers"
          stat-value="1 active"
          stat-description="Aktivní provider má jasný status, připojení i odpojení jsou oddělené akce a destruktivní CTA není primární."
        >
          <div class="auth-card">
            <div class="auth-card__eyebrow">Connections</div>
            <h2>Propojené účty</h2>
            <p>Spravuj, které externí účty můžeš použít pro přihlášení do EnduroBuddy.</p>

            <article class="auth-provider-row">
              <div class="auth-provider-row__meta">
                <div class="auth-provider-row__logo">G</div>
                <div>
                  <strong>Google</strong>
                  <p>vojta@gmail.com · naposledy použito dnes</p>
                </div>
              </div>
              <div class="auth-provider-row__actions">
                <span class="auth-chip auth-chip--blue">Connected</span>
                <button class="auth-button auth-button--secondary" type="button">Odpojit</button>
              </div>
            </article>

            <article class="auth-provider-row">
              <div class="auth-provider-row__meta">
                <div class="auth-provider-row__logo auth-provider-row__logo--dark">+</div>
                <div>
                  <strong>Připojit další účet</strong>
                  <p>Rozšiř přístupové možnosti bez změny primární identity.</p>
                </div>
              </div>
              <div class="auth-provider-row__actions">
                <button class="auth-button auth-button--primary" type="button">Připojit Google</button>
              </div>
            </article>
          </div>
        </AuthPreviewShell>

        <AuthPreviewShell
          v-else
          brand-eyebrow="Fallback System"
          brand-title="Logout, inactive account i rate limit držíme v jedné rodině."
          brand-description="Tyto stránky nepotřebují vlastní layout. Stačí status varianty, které sdílí shell, typografii i CTA rytmus."
          stat-label="Utility States"
          stat-value="Shared shell"
          stat-description="Menší implementační plocha a mnohem konzistentnější auth experience."
        >
          <div class="auth-card auth-card--stacked">
            <div class="auth-status">
              <div class="auth-status__icon">→</div>
              <div>
                <div class="auth-chip">Logout</div>
                <strong>Opravdu se chceš odhlásit?</strong>
                <p>Jasné potvrzení bez rušivých prvků navíc.</p>
              </div>
            </div>

            <div class="auth-status auth-status--danger">
              <div class="auth-status__icon">×</div>
              <div>
                <div class="auth-chip auth-chip--danger">Inactive</div>
                <strong>Tento účet zatím není aktivní</strong>
                <p>K dispozici je cesta na support nebo resend verification.</p>
              </div>
            </div>

            <div class="auth-status auth-status--blue">
              <div class="auth-status__icon">⏱</div>
              <div>
                <div class="auth-chip auth-chip--blue">Rate limit</div>
                <strong>Zkus to prosím za chvíli znovu</strong>
                <p>Klidný wording a neutrální tón místo tvrdé error stránky.</p>
              </div>
            </div>
          </div>
        </AuthPreviewShell>
      </div>
    </section>
  </main>
</template>

<style scoped>
.auth-preview-page {
  min-height: 100vh;
  padding: 2rem 1rem 3rem;
  background:
    radial-gradient(circle at top right, rgba(200, 255, 0, 0.12), transparent 20rem),
    radial-gradient(circle at bottom left, rgba(56, 189, 248, 0.1), transparent 22rem),
    linear-gradient(180deg, #0c0c10 0%, var(--eb-bg) 100%);
}

.auth-preview-page__hero,
.auth-preview-page__body {
  width: min(100%, 88rem);
  margin: 0 auto;
}

.auth-preview-page__hero {
  padding: 2rem 2.25rem;
  margin-bottom: 1.5rem;
  border: 1px solid var(--eb-border);
  border-radius: 2rem;
  background: rgba(17, 17, 19, 0.82);
  backdrop-filter: blur(20px);
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.3);
}

.auth-preview-page__eyebrow {
  color: var(--eb-text-muted);
  font-size: var(--eb-type-label-size);
  font-weight: 700;
  letter-spacing: calc(var(--eb-type-label-tracking) + 0.03em);
  text-transform: uppercase;
}

.auth-preview-page__hero h1 {
  margin: 1rem 0 0.75rem;
  max-width: 11ch;
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-display-size);
  font-weight: var(--eb-type-display-weight);
  line-height: var(--eb-type-display-line);
  letter-spacing: var(--eb-type-display-tracking);
}

.auth-preview-page__hero p {
  max-width: 68ch;
  margin: 0;
  color: var(--eb-text-soft);
  font-size: var(--eb-type-body-size);
  line-height: var(--eb-type-body-line);
}

.auth-preview-page__body {
  display: grid;
  grid-template-columns: 17rem minmax(0, 1fr);
  gap: 1.5rem;
  align-items: start;
}

.auth-preview-nav {
  position: sticky;
  top: 1rem;
  display: grid;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid var(--eb-border);
  border-radius: 1.5rem;
  background: rgba(17, 17, 19, 0.76);
  backdrop-filter: blur(18px);
}

.auth-preview-nav__head {
  display: grid;
  gap: 0.35rem;
}

.auth-preview-nav__head strong {
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-h2-size);
  font-weight: var(--eb-type-h2-weight);
  letter-spacing: var(--eb-type-h2-tracking);
}

.auth-preview-nav__head span {
  color: var(--eb-text-soft);
  font-size: var(--eb-type-small-size);
  line-height: var(--eb-type-small-line);
}

.auth-preview-nav__list {
  display: grid;
  gap: 0.55rem;
}

.auth-preview-nav__item {
  display: grid;
  gap: 0.2rem;
  width: 100%;
  padding: 0.8rem 0.9rem;
  border: 1px solid var(--eb-border);
  border-radius: 1rem;
  background: rgba(9, 9, 11, 0.52);
  color: var(--eb-text);
  text-align: left;
  transition:
    transform 160ms ease,
    border-color 160ms ease,
    background 160ms ease;
}

.auth-preview-nav__item span {
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-h3-size);
  font-weight: 600;
  letter-spacing: var(--eb-type-h3-tracking);
}

.auth-preview-nav__item small {
  color: var(--eb-text-muted);
  font-size: var(--eb-type-small-size);
  line-height: var(--eb-type-small-line);
}

.auth-preview-nav__item:hover,
.auth-preview-nav__item.is-active {
  transform: translateY(-1px);
  border-color: rgba(200, 255, 0, 0.24);
  background: linear-gradient(180deg, rgba(200, 255, 0, 0.1) 0%, rgba(200, 255, 0, 0.04) 100%);
}

.auth-preview-stage {
  min-width: 0;
}

.auth-card {
  display: grid;
  gap: 1rem;
}

.auth-card--stacked {
  gap: 0.85rem;
}

.auth-card__eyebrow,
.auth-field span,
.auth-chip {
  font-size: var(--eb-type-label-size);
  font-weight: 700;
  letter-spacing: var(--eb-type-label-tracking);
  text-transform: uppercase;
}

.auth-card__eyebrow,
.auth-field span {
  color: var(--eb-text-muted);
}

.auth-card h2 {
  margin: -0.1rem 0 0;
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-h1-size);
  font-weight: var(--eb-type-h1-weight);
  line-height: var(--eb-type-h1-line);
  letter-spacing: var(--eb-type-h1-tracking);
}

.auth-card p,
.auth-footer,
.auth-provider-row p,
.auth-role-card p,
.auth-status p {
  margin: 0;
  color: var(--eb-text-soft);
  font-size: var(--eb-type-body-size);
  line-height: var(--eb-type-body-line);
}

.auth-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.auth-grid--actions {
  margin-top: 0.35rem;
}

.auth-field {
  display: grid;
  gap: 0.45rem;
}

.auth-field input,
.auth-field select {
  width: 100%;
  min-height: 3rem;
  border: 1px solid var(--eb-border);
  border-radius: 0.7rem;
  padding: 0.8rem 0.9rem;
  background: #09090b;
  color: var(--eb-text);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.02);
}

.auth-field input.is-imported {
  border-color: rgba(56, 189, 248, 0.24);
  background: linear-gradient(180deg, rgba(56, 189, 248, 0.08) 0%, rgba(9, 9, 11, 1) 100%);
}

.auth-field small {
  color: var(--eb-text-muted);
  font-size: var(--eb-type-small-size);
}

.auth-field small.is-danger {
  color: #fda4af;
}

.auth-inline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.auth-inline a,
.auth-footer button {
  color: var(--eb-lime);
  font-size: var(--eb-type-small-size);
  font-weight: 600;
}

.auth-divider {
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

.auth-divider::before,
.auth-divider::after {
  content: "";
  height: 1px;
  background: var(--eb-border);
}

.auth-button,
.auth-preview-nav__item,
.auth-inline a,
.auth-footer button {
  cursor: pointer;
}

.auth-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.65rem;
  min-height: 3rem;
  width: 100%;
  padding: 0 1rem;
  border: 1px solid transparent;
  border-radius: 0.7rem;
  font-size: var(--eb-type-small-size);
  font-weight: 700;
  letter-spacing: 0.02em;
  transition:
    transform 160ms ease,
    background 160ms ease,
    border-color 160ms ease;
}

.auth-button:hover {
  transform: translateY(-1px);
}

.auth-button--primary {
  background: var(--eb-lime);
  color: #09090b;
  box-shadow: var(--eb-glow-lime);
}

.auth-button--secondary {
  border-color: var(--eb-border);
  background: transparent;
  color: var(--eb-text);
}

.auth-button--ghost {
  background: rgba(255, 255, 255, 0.04);
  color: var(--eb-text-soft);
}

.auth-button--google {
  justify-content: flex-start;
  border-color: rgba(255, 255, 255, 0.08);
  background: linear-gradient(180deg, #fbfbfc 0%, #e8e9ed 100%);
  color: #18181b;
}

.auth-google-badge,
.auth-status__icon,
.auth-provider-row__logo {
  display: grid;
  place-items: center;
}

.auth-google-badge {
  width: 1.4rem;
  height: 1.4rem;
  border-radius: 999px;
  background: #fff;
  color: #4285f4;
  font-size: 0.85rem;
  font-weight: 700;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.auth-check {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  color: var(--eb-text-soft);
  font-size: var(--eb-type-small-size);
}

.auth-check__box {
  display: grid;
  place-items: center;
  width: 1.1rem;
  height: 1.1rem;
  border: 1px solid rgba(200, 255, 0, 0.24);
  border-radius: 0.35rem;
  background: rgba(200, 255, 0, 0.1);
  color: var(--eb-lime);
  font-size: 0.75rem;
}

.auth-footer {
  text-align: center;
  font-size: var(--eb-type-small-size);
}

.auth-footer button,
.auth-inline a {
  border: 0;
  background: transparent;
  padding: 0;
}

.auth-status {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.85rem;
  padding: 1rem;
  border: 1px solid rgba(200, 255, 0, 0.18);
  border-radius: 1rem;
  background: linear-gradient(180deg, rgba(200, 255, 0, 0.08) 0%, rgba(200, 255, 0, 0.03) 100%);
}

.auth-status--blue {
  border-color: rgba(56, 189, 248, 0.22);
  background: linear-gradient(180deg, rgba(56, 189, 248, 0.08) 0%, rgba(56, 189, 248, 0.03) 100%);
}

.auth-status--danger {
  border-color: rgba(244, 63, 94, 0.24);
  background: linear-gradient(180deg, rgba(244, 63, 94, 0.1) 0%, rgba(244, 63, 94, 0.03) 100%);
}

.auth-status__icon {
  width: 3rem;
  height: 3rem;
  border-radius: 1rem;
  border: 1px solid currentColor;
  color: var(--eb-lime);
  font-family: var(--eb-font-display);
  font-size: 1.15rem;
}

.auth-status--blue .auth-status__icon {
  color: var(--eb-blue);
}

.auth-status--danger .auth-status__icon {
  color: #fda4af;
}

.auth-status strong,
.auth-provider-row strong,
.auth-role-card strong {
  display: block;
  margin-bottom: 0.35rem;
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-h3-size);
  font-weight: 600;
  letter-spacing: var(--eb-type-h3-tracking);
}

.auth-chip {
  display: inline-flex;
  width: fit-content;
  margin-bottom: 0.35rem;
  padding: 0.42rem 0.55rem;
  border: 1px solid rgba(200, 255, 0, 0.2);
  border-radius: 999px;
  background: rgba(200, 255, 0, 0.1);
  color: var(--eb-lime);
}

.auth-chip--blue {
  border-color: rgba(56, 189, 248, 0.2);
  background: rgba(56, 189, 248, 0.1);
  color: var(--eb-blue);
}

.auth-chip--danger {
  border-color: rgba(244, 63, 94, 0.22);
  background: rgba(244, 63, 94, 0.1);
  color: #fda4af;
}

.auth-role-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.auth-role-card {
  padding: 0.95rem;
  border: 1px solid var(--eb-border);
  border-radius: 1rem;
  background: rgba(9, 9, 11, 0.5);
}

.auth-role-card--lime {
  border-color: rgba(200, 255, 0, 0.18);
  background: linear-gradient(180deg, rgba(200, 255, 0, 0.1) 0%, rgba(200, 255, 0, 0.03) 100%);
}

.auth-role-card--blue {
  border-color: rgba(56, 189, 248, 0.2);
  background: linear-gradient(180deg, rgba(56, 189, 248, 0.1) 0%, rgba(56, 189, 248, 0.03) 100%);
}

.auth-provider-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.95rem;
  border: 1px solid var(--eb-border);
  border-radius: 1rem;
  background: rgba(9, 9, 11, 0.5);
}

.auth-provider-row__meta,
.auth-provider-row__actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.auth-provider-row__logo {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.85rem;
  background: #fff;
  color: #4285f4;
  font-size: 1rem;
  font-weight: 700;
}

.auth-provider-row__logo--dark {
  background: #111113;
  color: var(--eb-text);
  border: 1px solid var(--eb-border);
}

.auth-provider-row__actions .auth-button {
  width: auto;
  min-height: 2.35rem;
  font-size: var(--eb-type-small-size);
}

@media (max-width: 1080px) {
  .auth-preview-page__body {
    grid-template-columns: 1fr;
  }

  .auth-preview-nav {
    position: static;
  }
}

@media (max-width: 720px) {
  .auth-preview-page {
    padding-inline: 0.75rem;
  }

  .auth-preview-page__hero {
    padding: 1.5rem;
    border-radius: 1.5rem;
  }

  .auth-grid,
  .auth-role-grid {
    grid-template-columns: 1fr;
  }

  .auth-provider-row,
  .auth-provider-row__meta,
  .auth-provider-row__actions {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
