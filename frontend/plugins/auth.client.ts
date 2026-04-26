import { watch } from "vue"

import { useAuthStore } from "~/stores/auth"
import { useCoachStore } from "~/stores/coach"
import { useTrainingStore } from "~/stores/training"

export default defineNuxtPlugin(() => {
  const authStore = useAuthStore()
  const trainingStore = useTrainingStore()
  const coachStore = useCoachStore()

  watch(
    () => authStore.user?.id ?? null,
    (nextUserId, previousUserId) => {
      if (nextUserId === previousUserId) return
      trainingStore.resetDashboard()
      coachStore.resetDashboard()
    },
  )

  void authStore.initialize()
})
