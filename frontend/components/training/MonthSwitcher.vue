<script setup lang="ts">
import EbButton from "@/components/ui/EbButton.vue";

defineProps<{
  label: string;
  previousLabel?: string | null;
  nextLabel?: string | null;
  disabled?: boolean;
}>();

const emit = defineEmits<{
  previous: [];
  next: [];
}>();
</script>

<template>
  <div class="month-switcher">
    <EbButton variant="ghost" :disabled="!previousLabel || disabled" @click="emit('previous')">
      ← {{ previousLabel || "Older" }}
    </EbButton>
    <div class="month-switcher__label">{{ label }}</div>
    <EbButton variant="ghost" :disabled="!nextLabel || disabled" @click="emit('next')">
      {{ nextLabel || "Newer" }} →
    </EbButton>
  </div>
</template>

<style scoped>
.month-switcher {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.month-switcher__label {
  min-width: 10rem;
  text-align: center;
  font-family: var(--eb-font-display);
  font-size: 1rem;
  font-weight: 700;
}

@media (max-width: 767px) {
  .month-switcher {
    flex-direction: column;
    align-items: stretch;
  }

  .month-switcher__label {
    min-width: 0;
  }
}
</style>
