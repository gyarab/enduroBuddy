import { resolve } from "path"

export default defineNuxtConfig({
  compatibilityDate: "2024-11-01",
  devtools: { enabled: true },

  components: [
    { path: "~/components", pathPrefix: false },
  ],

  modules: [
    "@pinia/nuxt",
    "@nuxtjs/i18n",
  ],

  app: {
    head: {
      titleTemplate: '%s | EnduroBuddy',
      title: 'EnduroBuddy',
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/brand/eb-mark.svg' },
        { rel: "preconnect", href: "https://fonts.googleapis.com" },
        { rel: "preconnect", href: "https://fonts.gstatic.com", crossorigin: "" },
        {
          rel: "stylesheet",
          href: "https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800&family=Nunito:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap&subset=latin,latin-ext",
        },
      ],
    },
  },

  routeRules: {
    "/": { ssr: true },
    "/about": { ssr: true },
    "/terms": { ssr: true },
    "/privacy": { ssr: true },
    "/dashboard": { ssr: false },
    "/app/**": { ssr: false },
    "/coach/**": { ssr: false },
    "/accounts/**": { ssr: false },
  },

  runtimeConfig: {
    public: {
      apiBase: "/api/v1",
      appHost: "",
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
    "~/assets/css/public-base.css",
    "~/assets/css/public-home.css",
    "~/assets/css/public-about.css",
    "~/assets/css/public-legal.css",
  ],

  alias: {
    "@": resolve(__dirname, "./"),
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
