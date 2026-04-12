<template>
  <div class="week-skeleton">
    <div class="week-skeleton__header">
      <div class="week-skeleton__bar week-skeleton__bar--title" />
      <div class="week-skeleton__bar week-skeleton__bar--stats" />
    </div>

    <div class="week-skeleton__columns">
      <div class="week-skeleton__column">
        <div class="week-skeleton__label" />
        <div v-for="index in 3" :key="`planned-${index}`" class="week-skeleton__row" />
      </div>
      <div class="week-skeleton__column">
        <div class="week-skeleton__label" />
        <div v-for="index in 3" :key="`completed-${index}`" class="week-skeleton__row" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.week-skeleton {
  overflow: hidden;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-lg);
  background: var(--eb-surface);
}

.week-skeleton__header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--eb-border);
  background: var(--eb-surface-strong);
}

.week-skeleton__columns {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  padding: 1rem;
}

.week-skeleton__column {
  display: grid;
  gap: 0.75rem;
}

.week-skeleton__bar,
.week-skeleton__label,
.week-skeleton__row {
  border-radius: var(--eb-radius-md);
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 25%, rgba(255, 255, 255, 0.08) 50%, rgba(255, 255, 255, 0.03) 75%),
    var(--eb-surface-hover);
  background-size: 200% 100%;
  animation: shimmer 1.5s linear infinite;
}

.week-skeleton__bar--title {
  width: 9rem;
  height: 1rem;
}

.week-skeleton__bar--stats {
  width: 10rem;
  height: 1rem;
}

.week-skeleton__label {
  width: 5rem;
  height: 0.75rem;
}

.week-skeleton__row {
  height: 4.75rem;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }

  100% {
    background-position: -200% 0;
  }
}

@media (max-width: 1023px) {
  .week-skeleton__columns {
    grid-template-columns: 1fr;
  }
}
</style>
