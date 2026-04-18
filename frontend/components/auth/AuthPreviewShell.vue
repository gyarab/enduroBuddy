<script setup lang="ts">
defineProps<{
  brandEyebrow: string;
  brandTitle: string;
  brandDescription: string;
  stats?: Array<{ icon: string; label: string; value: string; blue?: boolean }>;
}>();
</script>

<template>
  <section class="auth-shell">
    <aside class="auth-shell__brand">
      <div class="auth-shell__grid-overlay" aria-hidden="true"></div>

      <div class="auth-shell__logo">
        <span class="auth-shell__mark" aria-hidden="true">
          <span></span>
          <span></span>
          <span></span>
        </span>
        <span>EnduroBuddy</span>
      </div>

      <div class="auth-shell__copy">
        <div class="auth-shell__eyebrow">{{ brandEyebrow }}</div>
        <h2>{{ brandTitle }}</h2>
        <p>{{ brandDescription }}</p>
      </div>

      <div v-if="stats?.length" class="auth-shell__stats">
        <div
          v-for="stat in stats"
          :key="stat.label"
          class="auth-shell__stat"
        >
          <div class="auth-shell__stat-icon" :class="{ 'auth-shell__stat-icon--blue': stat.blue }">
            {{ stat.icon }}
          </div>
          <div>
            <div class="auth-shell__stat-label">{{ stat.label }}</div>
            <div class="auth-shell__stat-value">{{ stat.value }}</div>
          </div>
        </div>
      </div>

      <slot name="brand-extra" />
    </aside>

    <div class="auth-shell__content">
      <div class="auth-shell__card">
        <slot />
      </div>
    </div>
  </section>
</template>

<style scoped>
.auth-shell {
  display: grid;
  grid-template-columns: minmax(19rem, 1.02fr) minmax(0, 1fr);
  min-height: 41rem;
  overflow: hidden;
  border: 1px solid var(--eb-border);
  border-radius: 1.5rem;
  background: linear-gradient(180deg, rgba(24, 24, 27, 0.98) 0%, rgba(14, 14, 16, 0.98) 100%);
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.42);
}

.auth-shell__brand {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.75rem;
  border-right: 1px solid var(--eb-border);
  background:
    radial-gradient(ellipse at 80% 15%, rgba(200, 255, 0, 0.10) 0%, transparent 55%),
    radial-gradient(ellipse at 10% 88%, rgba(56, 189, 248, 0.07) 0%, transparent 50%),
    var(--eb-bg);
  overflow: hidden;
}

.auth-shell__grid-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: radial-gradient(ellipse at 40% 40%, rgba(0, 0, 0, 0.55) 30%, transparent 75%);
  pointer-events: none;
}

.auth-shell__logo {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-h3-size);
  font-weight: 700;
  letter-spacing: var(--eb-type-h3-tracking);
}

.auth-shell__mark {
  display: inline-flex;
  align-items: flex-end;
  gap: 0.2rem;
  height: 1.15rem;
  transform: skewX(-6deg);
}

.auth-shell__mark span {
  width: 0.3125rem;
  border-radius: 0.15rem;
  background: var(--eb-lime);
  box-shadow: 0 0 10px rgba(200, 255, 0, 0.20);
}

.auth-shell__mark span:nth-child(1) { height: 0.44rem; opacity: 0.35; }
.auth-shell__mark span:nth-child(2) { height: 0.75rem; opacity: 0.65; }
.auth-shell__mark span:nth-child(3) { height: 1.15rem; }

.auth-shell__copy {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 0.875rem;
  margin-top: auto;
  max-width: 30ch;
}

.auth-shell__eyebrow {
  color: var(--eb-text-muted);
  font-size: var(--eb-type-label-size);
  font-weight: 700;
  letter-spacing: calc(var(--eb-type-label-tracking) + 0.03em);
  text-transform: uppercase;
}

.auth-shell__copy h2 {
  margin: 0;
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-h1-size);
  font-weight: var(--eb-type-h1-weight);
  line-height: var(--eb-type-h1-line);
  letter-spacing: var(--eb-type-h1-tracking);
}

.auth-shell__copy p {
  margin: 0;
  color: var(--eb-text-soft);
  font-size: var(--eb-type-body-size);
  line-height: var(--eb-type-body-line);
}

.auth-shell__stats {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 0.625rem;
}

.auth-shell__stat {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 0.875rem;
  border: 1px solid var(--eb-border);
  border-radius: 0.75rem;
  background: rgba(9, 9, 11, 0.5);
}

.auth-shell__stat-icon {
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  background: rgba(200, 255, 0, 0.10);
  border: 1px solid rgba(200, 255, 0, 0.18);
  display: grid;
  place-items: center;
  font-size: 0.9375rem;
  flex-shrink: 0;
}

.auth-shell__stat-icon--blue {
  background: rgba(56, 189, 248, 0.10);
  border-color: rgba(56, 189, 248, 0.18);
}

.auth-shell__stat-label {
  font-size: 0.6875rem;
  color: var(--eb-text-muted);
  line-height: 1.3;
}

.auth-shell__stat-value {
  font-family: var(--eb-font-mono);
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--eb-text);
  letter-spacing: -0.01em;
}

.auth-shell__content {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.75rem;
}

.auth-shell__card {
  width: min(100%, 29rem);
  padding: 1.75rem;
  border: 1px solid var(--eb-border);
  border-radius: 1.25rem;
  background: linear-gradient(180deg, rgba(24, 24, 27, 0.98) 0%, rgba(16, 16, 18, 0.98) 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

@media (max-width: 960px) {
  .auth-shell {
    grid-template-columns: 1fr;
  }

  .auth-shell__brand {
    min-height: 14rem;
    border-right: 0;
    border-bottom: 1px solid var(--eb-border);
  }

  .auth-shell__copy h2 {
    font-size: var(--eb-type-h2-size);
  }
}
</style>
