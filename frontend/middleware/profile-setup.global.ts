export default defineNuxtRouteMiddleware((to) => {
  const authStore = useAuthStore()
  if (
    authStore.user?.needs_profile_setup &&
    !to.path.startsWith("/accounts/profile-setup")
  ) {
    return navigateTo("/accounts/profile-setup/")
  }
})
