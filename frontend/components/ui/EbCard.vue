<template>
  <section class="eb-card">
    <slot />
  </section>
</template>

<style scoped>
.eb-card {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent 24%), var(--eb-surface);
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-lg);
  box-shadow: var(--eb-shadow-soft);
}
</style>
