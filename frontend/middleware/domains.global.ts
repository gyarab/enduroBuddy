export default defineNuxtRouteMiddleware(async (to) => {
  const config = useRuntimeConfig()
  const appHost = config.public.appHost as string
  if (!appHost) return

  const currentHost = import.meta.server
    ? (useRequestHeaders()["host"] ?? "").split(":")[0]
    : window.location.hostname

  const isAppDomain = currentHost === appHost
  const isPublicDomain = !isAppDomain

  const APP_PATHS = ["/dashboard", "/app/", "/coach/"]
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

  // Redirect authenticated users from public pages to app domain
  if (import.meta.client) {
    const auth = useAuthStore()
    if (!auth.hasBootstrapped) {
      await auth.initialize()
    }

    const PUBLIC_PAGES = ["/", "/about", "/terms", "/privacy"]
    if (isPublicDomain && PUBLIC_PAGES.includes(to.path) && auth.isAuthenticated) {
      const target = auth.isCoach ? "/coach/plans" : "/dashboard"
      return navigateTo(`https://${appHost}${target}`, { external: true })
    }
  }
})
