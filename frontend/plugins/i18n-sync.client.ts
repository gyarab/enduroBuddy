export default defineNuxtPlugin((nuxtApp) => {
  const csrfToken = useCookie("endurobuddy_csrftoken")

  async function syncWithDjango(lang: string) {
    try {
      await $fetch("/i18n/set_language/", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          ...(csrfToken.value ? { "X-CSRFToken": csrfToken.value } : {}),
        },
        body: `language=${lang}`,
      })
    } catch {
      // Non-critical — jazyk je přepnutý v Nuxtu
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const locale = (nuxtApp.$i18n as any)?.locale
  if (locale) {
    watch(locale, (newLocale: string) => {
      void syncWithDjango(newLocale)
    })
  }
})
