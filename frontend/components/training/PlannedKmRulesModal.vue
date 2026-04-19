<template>
  <Teleport to="body">
    <div
      v-if="isOpen"
      class="eb-modal-overlay"
      @click.self="$emit('close')"
    >
      <div class="eb-modal" role="dialog" aria-modal="true" aria-labelledby="km-rules-modal-title">
        <div class="eb-modal-header">
          <h2 id="km-rules-modal-title" class="eb-modal-title">{{ t("kmRules.title") }}</h2>
          <button class="eb-modal-close" @click="$emit('close')" :aria-label="t('kmRules.close')">✕</button>
        </div>
        <div class="eb-modal-body km-rules-body">
          <section>
            <h3>{{ t("kmRules.basicTitle") }}</h3>
            <ul>
              <li><code>15</code> — {{ t("kmRules.basicKm") }}</li>
              <li><code>1:30</code> — {{ t("kmRules.basicTime") }}</li>
              <li><code>15 / 1:30</code> — {{ t("kmRules.basicBoth") }}</li>
            </ul>
          </section>
          <section>
            <h3>{{ t("kmRules.typeTitle") }}</h3>
            <ul>
              <li><code>15 Z</code> — {{ t("kmRules.typeZ") }}</li>
              <li><code>15 T</code> — {{ t("kmRules.typeT") }}</li>
              <li><code>15 TV</code> — {{ t("kmRules.typeTV") }}</li>
            </ul>
          </section>
          <section>
            <h3>{{ t("kmRules.intervalsTitle") }}</h3>
            <ul>
              <li><code>10 + 5×1 Z</code> — {{ t("kmRules.intervalsExample") }}</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

const props = defineProps<{ isOpen: boolean }>()
const emit = defineEmits<{ close: [] }>()
const { t } = useI18n()

function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.isOpen) emit('close')
}
onMounted(() => document.addEventListener('keydown', onKeyDown))
onUnmounted(() => document.removeEventListener('keydown', onKeyDown))
</script>

<style scoped>
.eb-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.eb-modal {
  background: var(--eb-surface);
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-lg);
  width: min(520px, 90vw);
  max-height: 80vh;
  overflow-y: auto;
}
.eb-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--eb-border);
}
.eb-modal-title {
  font-family: var(--eb-font-display);
  font-size: 1.125rem;
  color: var(--eb-text);
  margin: 0;
}
.eb-modal-close {
  background: none;
  border: none;
  color: var(--eb-text-muted);
  cursor: pointer;
  font-size: 1rem;
  padding: 0.25rem;
}
.eb-modal-body {
  padding: 1.5rem;
}
.km-rules-body section {
  margin-bottom: 1.5rem;
}
.km-rules-body h3 {
  color: var(--eb-text);
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}
.km-rules-body ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.km-rules-body li {
  color: var(--eb-text-muted);
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
}
.km-rules-body code {
  font-family: var(--eb-font-mono);
  color: var(--eb-lime);
}
</style>
