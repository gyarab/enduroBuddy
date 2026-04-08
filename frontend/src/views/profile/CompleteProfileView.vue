<script setup lang="ts">
import EbButton from "@/components/ui/EbButton.vue";
import EbCard from "@/components/ui/EbCard.vue";
</script>

<template>
  <section class="profile-view">
    <EbCard class="profile-card">
      <div class="profile-card__eyebrow">Profile completion</div>
      <h1 class="profile-card__title">Tady navazeme Vue flow pro dokonceni profilu.</h1>
      <p class="profile-card__text">
        Zatim zustava auth a existujici allauth backend zachovany, jen mame pripravenou routu a shell.
      </p>
      <EbButton>Pokracovat</EbButton>
    </EbCard>
  </section>
</template>

<style scoped>
.profile-view {
  display: grid;
}

.profile-card {
  padding: 1.5rem;
}

.profile-card__eyebrow {
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.profile-card__title {
  margin: 0.75rem 0 0;
  font-family: var(--eb-font-display);
  font-size: clamp(1.75rem, 3vw, 2.3rem);
}

.profile-card__text {
  max-width: 38rem;
  color: var(--eb-text-soft);
  line-height: 1.6;
}
</style>
