<template>
  <span class="eb-spinner" aria-hidden="true" />
</template>

<style scoped>
.eb-spinner {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border-radius: 999px;
  border: 2px solid rgba(250, 250, 250, 0.22);
  border-top-color: var(--eb-lime);
  animation: spin 800ms linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
