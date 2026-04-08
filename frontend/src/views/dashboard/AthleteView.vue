<script setup lang="ts">
import EbBadge from "@/components/ui/EbBadge.vue";
import EbButton from "@/components/ui/EbButton.vue";
import EbCard from "@/components/ui/EbCard.vue";
</script>

<template>
  <section class="dashboard-view">
    <div class="dashboard-view__summary">
      <EbCard class="summary-card">
        <div class="summary-card__label">Treninky</div>
        <div class="summary-card__value">0 / 0</div>
        <div class="summary-card__meta">Read-only shell ready</div>
      </EbCard>
      <EbCard class="summary-card">
        <div class="summary-card__label">Kilometry</div>
        <div class="summary-card__value">0 km</div>
        <div class="summary-card__meta">Data endpoint prijde v dalsim kroku</div>
      </EbCard>
      <EbCard class="summary-card">
        <div class="summary-card__label">Cas</div>
        <div class="summary-card__value">0h 00m</div>
        <div class="summary-card__meta">Vue shell bezi nad Django routou</div>
      </EbCard>
      <EbCard class="summary-card">
        <div class="summary-card__label">Splneni</div>
        <div class="summary-card__value summary-card__value--highlight">0 %</div>
        <div class="summary-card__meta">Neon Lab x Swiss Precision</div>
      </EbCard>
    </div>

    <EbCard class="week-card">
      <div class="week-card__header">
        <div>
          <div class="week-card__eyebrow">Tyden 14</div>
          <div class="week-card__range">31. 3. - 6. 4.</div>
        </div>
        <div class="week-card__stats">0 km · 0h 00m</div>
      </div>

      <div class="week-card__body">
        <article class="training-row training-row--planned">
          <div class="training-row__main">
            <div>
              <div class="training-row__title">Tempo beh</div>
              <div class="training-row__notes">API dashboard payload sem napojime v dalsim slice.</div>
            </div>
            <div class="training-row__metrics">15 km · 70 min</div>
          </div>
          <div class="training-row__meta">
            <EbBadge tone="planned">Plan</EbBadge>
            <span class="training-row__day">Ct</span>
          </div>
        </article>

        <div class="week-card__footer">
          <EbButton variant="secondary">Pripravit dashboard data</EbButton>
        </div>
      </div>
    </EbCard>
  </section>
</template>

<style scoped>
.dashboard-view {
  display: grid;
  gap: 1rem;
}

.dashboard-view__summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1rem;
}

.summary-card {
  padding: 1rem 1.25rem;
}

.summary-card__label {
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.summary-card__value {
  margin-top: 0.5rem;
  font-family: var(--eb-font-mono);
  font-size: 1.375rem;
}

.summary-card__value--highlight {
  color: var(--eb-lime);
}

.summary-card__meta {
  margin-top: 0.35rem;
  color: var(--eb-text-muted);
  font-size: 0.75rem;
}

.week-card {
  overflow: hidden;
}

.week-card__header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.875rem 1.25rem;
  border-bottom: 1px solid var(--eb-border);
  background: var(--eb-surface-strong);
}

.week-card__eyebrow {
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.week-card__range,
.week-card__stats {
  margin-top: 0.2rem;
  color: var(--eb-text-soft);
  font-family: var(--eb-font-mono);
  font-size: 0.8125rem;
}

.week-card__body {
  padding: 1rem;
}

.training-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.875rem 1rem 0.875rem 0.875rem;
  border: 1px solid var(--eb-border);
  border-left-width: 3px;
  border-radius: var(--eb-radius-md);
  background: var(--eb-surface);
}

.training-row--planned {
  border-left-color: var(--eb-blue);
}

.training-row__main,
.training-row__meta {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.training-row__title {
  font-size: 0.9375rem;
  font-weight: 500;
}

.training-row__notes {
  margin-top: 0.2rem;
  color: var(--eb-text-muted);
  font-size: 0.75rem;
}

.training-row__metrics {
  color: var(--eb-text-soft);
  font-family: var(--eb-font-mono);
  font-size: 0.8125rem;
}

.training-row__day {
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.week-card__footer {
  margin-top: 1rem;
}

@media (max-width: 1023px) {
  .dashboard-view__summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 767px) {
  .dashboard-view__summary {
    grid-template-columns: 1fr;
  }

  .week-card__header,
  .training-row,
  .training-row__main,
  .training-row__meta {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
