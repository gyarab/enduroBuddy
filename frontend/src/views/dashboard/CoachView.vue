<script setup lang="ts">
import EbBadge from "@/components/ui/EbBadge.vue";
import EbCard from "@/components/ui/EbCard.vue";
</script>

<template>
  <section class="coach-view">
    <aside class="coach-view__sidebar">
      <EbCard class="sidebar-card">
        <div class="sidebar-card__header">Atleti</div>
        <button class="sidebar-card__row sidebar-card__row--active" type="button">
          <span class="sidebar-card__dot" />
          <span>Vybrany atlet</span>
          <EbBadge tone="done">Focus</EbBadge>
        </button>
        <button class="sidebar-card__row" type="button">
          <span class="sidebar-card__dot sidebar-card__dot--muted" />
          <span>Dalsi atlet</span>
        </button>
      </EbCard>
    </aside>

    <div class="coach-view__content">
      <EbCard class="coach-card">
        <div class="coach-card__eyebrow">Coach workspace</div>
        <h1 class="coach-card__title">Shell pro `/coach/plans` je pripraveny.</h1>
        <p class="coach-card__text">
          Dalsi iterace napoji athlete focus, dashboard payload a sdilene week cards.
        </p>
      </EbCard>
    </div>
  </section>
</template>

<style scoped>
.coach-view {
  display: grid;
  grid-template-columns: 18rem minmax(0, 1fr);
  gap: 1rem;
}

.coach-view__sidebar {
  position: sticky;
  top: calc(var(--eb-topnav-height) + 1.5rem);
  align-self: start;
}

.sidebar-card {
  padding: 1rem 0;
}

.sidebar-card__header {
  padding: 0 1rem 0.75rem;
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.sidebar-card__row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.875rem 1rem;
  border: 0;
  border-left: 2px solid transparent;
  background: transparent;
  color: var(--eb-text-soft);
  text-align: left;
}

.sidebar-card__row:hover {
  background: var(--eb-surface-hover);
  color: var(--eb-text);
}

.sidebar-card__row--active {
  border-left-color: var(--eb-lime);
  background: rgba(200, 255, 0, 0.06);
  color: var(--eb-text);
}

.sidebar-card__dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 999px;
  background: var(--eb-lime);
}

.sidebar-card__dot--muted {
  background: var(--eb-border);
}

.coach-card {
  padding: 1.5rem;
}

.coach-card__eyebrow {
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.coach-card__title {
  margin: 0.75rem 0 0;
  font-family: var(--eb-font-display);
  font-size: clamp(1.75rem, 3vw, 2.5rem);
  line-height: 1;
}

.coach-card__text {
  max-width: 38rem;
  margin: 1rem 0 0;
  color: var(--eb-text-soft);
  line-height: 1.6;
}

@media (max-width: 1023px) {
  .coach-view {
    grid-template-columns: 1fr;
  }

  .coach-view__sidebar {
    position: static;
  }
}
</style>
