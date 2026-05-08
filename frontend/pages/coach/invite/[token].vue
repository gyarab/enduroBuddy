<template>
  <InviteView />
</template>

<script setup lang="ts">
definePageMeta({ layout: "default" })

const { t } = useI18n()
useHead({ title: computed(() => t('page.invite')) })
</script>
