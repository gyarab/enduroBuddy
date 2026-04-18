export default defineNuxtPlugin(() => {
  const { locale } = useI18n()

  async function syncWithDjango(lang: string) {
    const csrfToken = useCookie("endurobuddy_csrftoken")
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

  watch(locale, (newLocale) => {
    void syncWithDjango(newLocale)
  })
})
