import { useAuthStore } from "~/stores/auth"

const PROTECTED_PATHS = ["/app/", "/coach/", "/dashboard"]

export default defineNuxtRouteMiddleware(async (to) => {
  if (import.meta.server) return

  const isProtected = PROTECTED_PATHS.some((p) => to.path === p || to.path.startsWith(p))
  if (!isProtected) return

  const auth = useAuthStore()
  if (!auth.hasBootstrapped) {
    await auth.initialize()
  }

  if (!auth.isAuthenticated) {
    const config = useRuntimeConfig()
    const appHost = config.public.appHost as string
    if (appHost) {
      const publicHost = appHost.replace(/^app\./, "")
      return navigateTo(`https://${publicHost}/accounts/login/`, { external: true })
    }
    return navigateTo("/accounts/login/")
  }
})
