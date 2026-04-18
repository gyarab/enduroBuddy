<template>
  <main style="padding: 96px 24px; text-align: center;">
    <h1>Soon</h1>
  </main>
</template>

<script setup lang="ts">
definePageMeta({ layout: "public" })

const { t } = useI18n()

useSeoMeta({
  title: t("about.seoTitle"),
})
</script>
