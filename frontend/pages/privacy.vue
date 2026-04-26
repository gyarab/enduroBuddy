<template>
  <main class="eb-legal-main">
    <div class="eb-legal-shell">
      <NuxtLink to="/" class="eb-legal-back">{{ t("legal.back") }}</NuxtLink>
      <div class="eb-legal-header">
        <div class="eb-legal-kicker">{{ t("legal.kicker") }}</div>
      </div>
      <article class="eb-legal-card">
        <template v-if="locale === 'en'">
          <h1 class="eb-legal-title">Privacy Policy</h1>
          <p class="eb-legal-lead">EnduroBuddy - effective from April 1, 2026</p>

          <section class="eb-legal-section">
            <h2>1. Controller of personal data</h2>
            <p class="eb-legal-copy">
              The controller of personal data is:<br>
              <strong>Name:</strong> Vojtěch Holcman<br>
              <strong>Address:</strong> K lánu 496/2, 160 00 Praha 6, Czech Republic<br>
              <strong>Email:</strong> support@endurobuddy.cz
            </p>
          </section>

          <section class="eb-legal-section">
            <h2>2. What personal data we process</h2>
            <p class="eb-legal-copy">We process the following categories of personal data:</p>
            <p class="eb-legal-copy"><strong>Registration and profile data</strong></p>
            <ul class="eb-legal-list">
              <li>first name and last name</li>
              <li>email address</li>
              <li>role in the application, coach or athlete</li>
              <li>login credentials, including a securely protected password</li>
              <li>optionally, Google profile data when signing in with Google</li>
            </ul>
            <p class="eb-legal-copy"><strong>Training and performance data</strong></p>
            <ul class="eb-legal-list">
              <li>planned sessions, including date, title, distance, notes, and two-phase days</li>
              <li>completed sessions, including time, distance, average heart rate, subjective feeling, and notes</li>
              <li>imported activity data from FIT files or Garmin</li>
              <li>metadata of imported files, including the original filename</li>
            </ul>
            <p class="eb-legal-copy"><strong>Garmin Connect integration (optional)</strong></p>
            <ul class="eb-legal-list">
              <li>Garmin email and displayed name</li>
              <li>securely stored credentials needed for Garmin Connect connection</li>
            </ul>
          </section>

          <section class="eb-legal-section">
            <h2>3. Purpose and legal basis of processing</h2>
            <table>
              <thead><tr><th>Purpose</th><th>Legal basis under GDPR</th></tr></thead>
              <tbody>
                <tr><td>Provision of the service</td><td>Performance of a contract under Article 6(1)(b)</td></tr>
                <tr><td>Connection to Garmin Connect</td><td>Consent under Article 6(1)(a)</td></tr>
                <tr><td>Sending transactional emails</td><td>Performance of a contract under Article 6(1)(b)</td></tr>
                <tr><td>Ensuring service security</td><td>Legitimate interest under Article 6(1)(f)</td></tr>
                <tr><td>Compliance with legal obligations</td><td>Legal obligation under Article 6(1)(c)</td></tr>
              </tbody>
            </table>
          </section>

          <section class="eb-legal-section">
            <h2>4. Recipients of personal data</h2>
            <ul class="eb-legal-list">
              <li><strong>Hosting and infrastructure providers</strong> — EU-based providers</li>
              <li><strong>Google sign-in provider</strong> — if you use sign-in with Google</li>
              <li><strong>Email delivery provider</strong> — for transactional emails</li>
              <li><strong>Garmin Connect provider</strong> — if you connect Garmin</li>
            </ul>
            <p class="eb-legal-copy">We do not sell personal data.</p>
          </section>

          <section class="eb-legal-section">
            <h2>5. Data retention</h2>
            <table>
              <thead><tr><th>Data category</th><th>Retention period</th></tr></thead>
              <tbody>
                <tr><td>Registration and profile data</td><td>Duration of account + 30 days after deletion</td></tr>
                <tr><td>Training and performance data</td><td>Duration of account + 30 days after deletion</td></tr>
                <tr><td>Garmin Connect credentials</td><td>Until disconnection or account deletion</td></tr>
                <tr><td>Operational and security logs</td><td>Up to 90 days</td></tr>
              </tbody>
            </table>
          </section>

          <section class="eb-legal-section">
            <h2>6. Your rights</h2>
            <p class="eb-legal-copy">You have the right to access, rectify, erase, restrict processing, data portability, and object. Contact: <a href="mailto:support@endurobuddy.cz">support@endurobuddy.cz</a></p>
            <p class="eb-legal-copy">Supervisory authority: Úřad pro ochranu osobních údajů, Pplk. Sochora 27, 170 00 Praha 7, <a href="https://www.uoou.cz" target="_blank" rel="noreferrer">www.uoou.cz</a></p>
          </section>

          <section class="eb-legal-section">
            <h2>7. Changes</h2>
            <p class="eb-legal-copy">We will inform you of material changes at least 30 days before they take effect.</p>
          </section>
        </template>

        <template v-else>
          <h1 class="eb-legal-title">Zásady ochrany osobních údajů</h1>
          <p class="eb-legal-lead">EnduroBuddy - účinné od 1. 4. 2026</p>

          <section class="eb-legal-section">
            <h2>1. Správce osobních údajů</h2>
            <p class="eb-legal-copy">
              Správcem osobních údajů je:<br>
              <strong>Jméno:</strong> Vojtěch Holcman<br>
              <strong>Adresa:</strong> K lánu 496/2, 160 00 Praha 6, Česká republika<br>
              <strong>E-mail:</strong> support@endurobuddy.cz
            </p>
          </section>

          <section class="eb-legal-section">
            <h2>2. Jaké osobní údaje zpracováváme</h2>
            <p class="eb-legal-copy"><strong>Registrační a profilové údaje</strong></p>
            <ul class="eb-legal-list">
              <li>jméno a příjmení</li>
              <li>e-mailová adresa</li>
              <li>role v aplikaci, trenér nebo sportovec</li>
              <li>přihlašovací údaje včetně bezpečně chráněného hesla</li>
              <li>volitelně Google profil při přihlášení přes Google</li>
            </ul>
            <p class="eb-legal-copy"><strong>Tréninková a výkonnostní data</strong></p>
            <ul class="eb-legal-list">
              <li>plánované a splněné tréninky</li>
              <li>importované aktivity ze souborů FIT nebo Garminu</li>
              <li>metadata importovaných souborů</li>
            </ul>
            <p class="eb-legal-copy"><strong>Garmin Connect integrace (volitelná)</strong></p>
            <ul class="eb-legal-list">
              <li>Garmin e-mail a zobrazované jméno</li>
              <li>bezpečně uložené údaje pro propojení s Garmin Connect</li>
            </ul>
          </section>

          <section class="eb-legal-section">
            <h2>3. Účel a právní základ zpracování</h2>
            <table>
              <thead><tr><th>Účel</th><th>Právní základ podle GDPR</th></tr></thead>
              <tbody>
                <tr><td>Poskytování služby</td><td>Plnění smlouvy podle čl. 6 odst. 1 písm. b)</td></tr>
                <tr><td>Propojení s Garmin Connect</td><td>Souhlas podle čl. 6 odst. 1 písm. a)</td></tr>
                <tr><td>Zasílání transakčních e-mailů</td><td>Plnění smlouvy podle čl. 6 odst. 1 písm. b)</td></tr>
                <tr><td>Zajištění bezpečnosti služby</td><td>Oprávněný zájem podle čl. 6 odst. 1 písm. f)</td></tr>
                <tr><td>Plnění zákonných povinností</td><td>Právní povinnost podle čl. 6 odst. 1 písm. c)</td></tr>
              </tbody>
            </table>
          </section>

          <section class="eb-legal-section">
            <h2>4. Příjemci osobních údajů</h2>
            <ul class="eb-legal-list">
              <li><strong>Poskytovatelé hostingu a infrastruktury</strong> — umístění v EU</li>
              <li><strong>Poskytovatel přihlášení přes Google</strong> — pokud využijete Google přihlášení</li>
              <li><strong>Poskytovatel e-mailových služeb</strong> — transakční e-maily</li>
              <li><strong>Poskytovatel Garmin Connect</strong> — pokud propojíte Garmin</li>
            </ul>
            <p class="eb-legal-copy">Osobní údaje neprodáváme.</p>
          </section>

          <section class="eb-legal-section">
            <h2>5. Doba uchovávání</h2>
            <table>
              <thead><tr><th>Kategorie dat</th><th>Doba uchovávání</th></tr></thead>
              <tbody>
                <tr><td>Registrační a profilové údaje</td><td>Po dobu účtu + 30 dní po smazání</td></tr>
                <tr><td>Tréninková data</td><td>Po dobu účtu + 30 dní po smazání</td></tr>
                <tr><td>Údaje Garmin Connect</td><td>Do odpojení nebo smazání účtu</td></tr>
                <tr><td>Provozní a bezpečnostní logy</td><td>Maximálně 90 dní</td></tr>
              </tbody>
            </table>
          </section>

          <section class="eb-legal-section">
            <h2>6. Vaše práva</h2>
            <p class="eb-legal-copy">Máte právo na přístup, opravu, výmaz, omezení zpracování, přenositelnost a námitku. Kontakt: <a href="mailto:support@endurobuddy.cz">support@endurobuddy.cz</a></p>
            <p class="eb-legal-copy">Dozorový úřad: Úřad pro ochranu osobních údajů, Pplk. Sochora 27, 170 00 Praha 7, <a href="https://www.uoou.cz" target="_blank" rel="noreferrer">www.uoou.cz</a></p>
          </section>

          <section class="eb-legal-section">
            <h2>7. Změny těchto zásad</h2>
            <p class="eb-legal-copy">O podstatných změnách Vás budeme informovat nejméně 30 dní před jejich účinností.</p>
          </section>
        </template>
      </article>
    </div>
  </main>
</template>

<script setup lang="ts">
definePageMeta({ layout: "public" })

const { t, locale } = useI18n()

useSeoMeta({
  title: locale.value === "en" ? "Privacy Policy | EnduroBuddy" : "Zásady ochrany osobních údajů | EnduroBuddy",
})
</script>
