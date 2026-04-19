import { resolve } from "path"

export default defineNuxtConfig({
  compatibilityDate: "2024-11-01",
  devtools: { enabled: true },

  modules: [
    "@pinia/nuxt",
    "@nuxtjs/i18n",
  ],

  routeRules: {
    "/": { ssr: true },
    "/about": { ssr: true },
    "/terms": { ssr: true },
    "/privacy": { ssr: true },
    "/app/**": { ssr: false },
    "/coach/**": { ssr: false },
    "/accounts/**": { ssr: false },
  },

  runtimeConfig: {
    public: {
      apiBase: "/api/v1",
    },
  },

  i18n: {
    locales: [
      { code: "cs", file: "cs.json" },
      { code: "en", file: "en.json" },
    ],
    defaultLocale: "cs",
    langDir: "locales/",
    strategy: "no_prefix",
    detectBrowserLanguage: false,
    bundle: {
      optimizeTranslationDirective: false,
    },
  },

  css: [
    "~/assets/design-tokens.css",
    "~/assets/fonts.css",
    "~/assets/css/public-base.css",
    "~/assets/css/public-home.css",
    "~/assets/css/public-about.css",
    "~/assets/css/public-legal.css",
  ],

  alias: {
    "@": resolve(__dirname, "./src"),
  },

  vite: {
    server: {
      proxy: {
        "/api": "http://localhost:8000",
        "/admin": "http://localhost:8000",
        "/accounts/google": "http://localhost:8000",
        "/i18n/set_language": "http://localhost:8000",
        "/static": "http://localhost:8000",
      },
    },
  },
})
