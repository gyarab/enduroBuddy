export default defineNuxtRouteMiddleware(async (to) => {
  const config = useRuntimeConfig()
  const appHost = config.public.appHost as string
  if (!appHost) return

  const currentHost = import.meta.server
    ? (useRequestHeaders()["host"] ?? "").split(":")[0]
    : window.location.hostname

  const isAppDomain = currentHost === appHost
  const isPublicDomain = !isAppDomain

  const APP_PATHS = ["/app/", "/coach/"]
  const isAppPath = APP_PATHS.some((p) => to.path.startsWith(p))

  // App domain + public path → redirect to public domain
  if (isAppDomain && !isAppPath) {
    const publicHost = appHost.replace(/^app\./, "")
    return navigateTo(`https://${publicHost}${to.fullPath}`, { external: true })
  }

  // Public domain + app path → redirect to app domain
  if (isPublicDomain && isAppPath) {
    return navigateTo(`https://${appHost}${to.fullPath}`, { external: true })
  }

  // Auth checks: client-side only to avoid SSR waterfall
  if (import.meta.client) {
    const auth = useAuthStore()
    if (!auth.hasBootstrapped) {
      await auth.initialize()
    }

    // Public domain + authenticated + public page → redirect to app domain
    const PUBLIC_PAGES = ["/", "/about", "/terms", "/privacy"]
    if (isPublicDomain && PUBLIC_PAGES.includes(to.path) && auth.isAuthenticated) {
      const target = auth.isCoach ? "/coach/plans" : "/app/dashboard"
      return navigateTo(`https://${appHost}${target}`, { external: true })
    }

    // App domain + not authenticated + app path → redirect to login on public domain
    if (isAppDomain && isAppPath && !auth.isAuthenticated) {
      const publicHost = appHost.replace(/^app\./, "")
      return navigateTo(`https://${publicHost}/accounts/login/`, { external: true })
    }
  }
})
