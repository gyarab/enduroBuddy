<template>
  <div class="eb-public-root">
    <header class="eb-topbar">
      <div class="eb-public-shell eb-topbar-inner">
        <NuxtLink to="/" class="eb-topbar-brand" aria-label="EnduroBuddy">
          <img src="/static/brand/eb-logo-full.svg" alt="EnduroBuddy" class="eb-logo-full">
          <img src="/static/brand/eb-logo-compact.svg" alt="EB" class="eb-logo-compact">
        </NuxtLink>

        <nav class="eb-topbar-nav" :aria-label="t('nav.mainNavLabel')">
          <slot name="nav">
            <NuxtLink to="/" class="eb-topbar-link">{{ t("nav.home") }}</NuxtLink>
            <NuxtLink to="/about" class="eb-topbar-link">{{ t("nav.about") }}</NuxtLink>
            <a href="/#features" class="eb-topbar-link">{{ t("nav.features") }}</a>
          </slot>
        </nav>

        <div class="eb-topbar-actions">
          <slot name="actions">
            <NuxtLink to="/accounts/login/" class="eb-btn-nav">
              {{ t("nav.login") }} →
            </NuxtLink>
          </slot>
        </div>
      </div>
    </header>

    <slot />

    <footer class="eb-footer">
      <div class="eb-public-shell">
        <div class="eb-footer-grid">
          <div class="eb-footer-brand">
            <img src="/static/brand/eb-logo-full.svg" alt="EnduroBuddy" class="eb-footer-logo">
            <p class="eb-footer-tagline">{{ t("footer.tagline") }}</p>
          </div>

          <nav class="eb-footer-nav" :aria-label="t('nav.footerNavLabel')">
            <ul>
              <li><NuxtLink to="/">{{ t("nav.home") }}</NuxtLink></li>
              <li><NuxtLink to="/about">{{ t("nav.about") }}</NuxtLink></li>
              <li><NuxtLink to="/terms">{{ t("nav.terms") }}</NuxtLink></li>
              <li><NuxtLink to="/privacy">{{ t("nav.privacy") }}</NuxtLink></li>
            </ul>
          </nav>

          <div class="eb-footer-lang">
            <div class="eb-footer-lang-label">{{ t("footer.language") }}</div>
            <div class="eb-footer-lang-pills">
              <button
                class="eb-lang-pill"
                :class="{ 'is-active': locale === 'cs' }"
                @click="setLocale('cs')"
              >CZ</button>
              <button
                class="eb-lang-pill"
                :class="{ 'is-active': locale === 'en' }"
                @click="setLocale('en')"
              >EN</button>
            </div>
          </div>
        </div>

        <div class="eb-footer-copy">© {{ currentYear }} EnduroBuddy</div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
const { t, locale, setLocale } = useI18n()

const currentYear = new Date().getFullYear()
</script>
