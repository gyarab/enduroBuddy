<template>
  <main class="eb-about-main">
    <div class="eb-about-shell">

      <!-- INTRO -->
      <section class="eb-about-intro">
        <div class="eb-about-kicker">{{ t("about.kicker") }}</div>
        <h1 class="eb-about-h1">{{ t("about.h1") }}</h1>
        <p class="eb-about-lead">{{ t("about.lead") }}</p>
      </section>

      <!-- STORY -->
      <section class="eb-about-story">
        <h2 class="eb-about-h2">{{ t("about.storyTitle") }}</h2>
        <p>{{ t("about.storyP1") }}</p>
        <p>{{ t("about.storyP2") }}</p>
        <p>{{ t("about.storyP3") }}</p>
      </section>

      <!-- MISSION -->
      <section class="eb-about-mission">
        <p class="eb-about-mission-statement">{{ t("about.missionStatement") }}</p>
        <ul class="eb-about-mission-list">
          <li class="coach">{{ t("about.missionCoach1") }}</li>
          <li class="coach">{{ t("about.missionCoach2") }}</li>
          <li class="athlete">{{ t("about.missionAthlete1") }}</li>
          <li class="athlete">{{ t("about.missionAthlete2") }}</li>
        </ul>
      </section>

      <!-- FOUNDER -->
      <div class="eb-about-founder">
        <div class="eb-about-avatar" aria-hidden="true">VH</div>
        <div>
          <div class="eb-about-founder-name">{{ t("about.founderName") }}</div>
          <div class="eb-about-founder-role">{{ t("about.founderRole") }}</div>
          <p class="eb-about-founder-quote">"{{ t("about.founderQuote") }}"</p>
        </div>
      </div>

    </div>
  </main>
</template>

<script setup lang="ts">
definePageMeta({ layout: "public" })

const { t } = useI18n()

useSeoMeta({
  title: t("about.seoTitle"),
  description: t("about.seoDescription"),
})
</script>
