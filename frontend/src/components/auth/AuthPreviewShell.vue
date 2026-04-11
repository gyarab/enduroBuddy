<script setup lang="ts">
defineProps<{
  brandEyebrow: string;
  brandTitle: string;
  brandDescription: string;
  statLabel?: string;
  statValue?: string;
  statDescription?: string;
}>();
</script>

<template>
  <section class="auth-preview-shell">
    <aside class="auth-preview-shell__brand">
      <div class="auth-preview-shell__logo">
        <span class="auth-preview-shell__mark" aria-hidden="true">
          <span></span>
          <span></span>
          <span></span>
        </span>
        <span>EnduroBuddy</span>
      </div>

      <div class="auth-preview-shell__brand-copy">
        <div class="auth-preview-shell__eyebrow">{{ brandEyebrow }}</div>
        <h2>{{ brandTitle }}</h2>
        <p>{{ brandDescription }}</p>
      </div>

      <div v-if="statLabel || statValue || statDescription" class="auth-preview-shell__stat">
        <div class="auth-preview-shell__stat-label">{{ statLabel }}</div>
        <strong v-if="statValue">{{ statValue }}</strong>
        <p v-if="statDescription">{{ statDescription }}</p>
      </div>

      <slot name="brand-extra" />
    </aside>

    <div class="auth-preview-shell__content">
      <div class="auth-preview-shell__card">
        <slot />
      </div>
    </div>
  </section>
</template>

<style scoped>
.auth-preview-shell {
  display: grid;
  grid-template-columns: minmax(19rem, 1.02fr) minmax(0, 1fr);
  min-height: 41rem;
  overflow: hidden;
  border: 1px solid var(--eb-border);
  border-radius: 1.5rem;
  background: linear-gradient(180deg, rgba(24, 24, 27, 0.98) 0%, rgba(14, 14, 16, 0.98) 100%);
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.42);
}

.auth-preview-shell__brand {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 1.5rem;
  padding: 1.75rem;
  border-right: 1px solid var(--eb-border);
  background:
    radial-gradient(circle at top right, rgba(200, 255, 0, 0.12), transparent 28%),
    radial-gradient(circle at bottom left, rgba(56, 189, 248, 0.12), transparent 28%),
    linear-gradient(180deg, rgba(12, 12, 14, 0.96) 0%, rgba(9, 9, 11, 1) 100%);
}

.auth-preview-shell__logo {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-h3-size);
  font-weight: 700;
  letter-spacing: var(--eb-type-h3-tracking);
}

.auth-preview-shell__mark {
  display: inline-flex;
  align-items: flex-end;
  gap: 0.25rem;
  height: 1.25rem;
}

.auth-preview-shell__mark span {
  width: 0.5rem;
  border-radius: 0.2rem;
  background: var(--eb-lime);
  transform: skewX(-9deg);
  box-shadow: 0 0 12px rgba(200, 255, 0, 0.18);
}

.auth-preview-shell__mark span:nth-child(1) {
  height: 0.5rem;
  opacity: 0.38;
}

.auth-preview-shell__mark span:nth-child(2) {
  height: 0.9rem;
  opacity: 0.68;
}

.auth-preview-shell__mark span:nth-child(3) {
  height: 1.25rem;
}

.auth-preview-shell__brand-copy {
  display: grid;
  gap: 1rem;
  max-width: 30ch;
}

.auth-preview-shell__eyebrow,
.auth-preview-shell__stat-label {
  color: var(--eb-text-muted);
  font-size: var(--eb-type-label-size);
  font-weight: 700;
  letter-spacing: calc(var(--eb-type-label-tracking) + 0.03em);
  text-transform: uppercase;
}

.auth-preview-shell__brand-copy h2 {
  margin: 0;
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-h1-size);
  font-weight: var(--eb-type-h1-weight);
  line-height: var(--eb-type-h1-line);
  letter-spacing: var(--eb-type-h1-tracking);
}

.auth-preview-shell__brand-copy p,
.auth-preview-shell__stat p {
  margin: 0;
  color: var(--eb-text-soft);
  font-size: var(--eb-type-body-size);
  line-height: var(--eb-type-body-line);
}

.auth-preview-shell__stat {
  padding: 1.125rem;
  border: 1px solid rgba(200, 255, 0, 0.18);
  border-radius: 1.125rem;
  background: linear-gradient(180deg, rgba(200, 255, 0, 0.1) 0%, rgba(200, 255, 0, 0.04) 100%);
}

.auth-preview-shell__stat strong {
  display: block;
  margin: 0.45rem 0;
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-h1-size);
  line-height: 1;
  letter-spacing: var(--eb-type-h1-tracking);
}

.auth-preview-shell__content {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.75rem;
}

.auth-preview-shell__card {
  width: min(100%, 29rem);
  padding: 1.75rem;
  border: 1px solid var(--eb-border-soft, var(--eb-border));
  border-radius: 1.25rem;
  background: linear-gradient(180deg, rgba(24, 24, 27, 0.98) 0%, rgba(16, 16, 18, 0.98) 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

@media (max-width: 960px) {
  .auth-preview-shell {
    grid-template-columns: 1fr;
  }

  .auth-preview-shell__brand {
    min-height: 16rem;
    border-right: 0;
    border-bottom: 1px solid var(--eb-border);
  }
}
</style>
