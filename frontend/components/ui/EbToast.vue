<template>
  <div class="eb-toast">
    <slot />
  </div>
</template>

<style scoped>
.eb-toast {
  padding: 0.875rem 1rem;
  border-radius: var(--eb-radius-md);
  border: 1px solid rgba(200, 255, 0, 0.16);
  background: rgba(17, 17, 19, 0.96);
  box-shadow: var(--eb-shadow-soft);
}
</style>
