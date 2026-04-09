import { computed, ref } from "vue";

import cs from "@/locales/cs.json";
import en from "@/locales/en.json";

type Locale = "cs" | "en";
type MessageTree = {
  [key: string]: string | MessageTree;
};

const messages = {
  cs,
  en,
} satisfies Record<Locale, MessageTree>;

const initialLocale = (() => {
  if (typeof document !== "undefined") {
    const lang = document.documentElement.lang.toLowerCase();
    return lang.startsWith("en") ? "en" : "cs";
  }
  return "cs";
})();

const currentLocale = ref<Locale>(initialLocale);

function resolvePath(source: MessageTree, path: string): string | null {
  const parts = path.split(".");
  let cursor: string | MessageTree | undefined = source;
  for (const part of parts) {
    if (!cursor || typeof cursor === "string" || !(part in cursor)) {
      return null;
    }
    cursor = cursor[part];
  }
  return typeof cursor === "string" ? cursor : null;
}

function interpolate(template: string, params?: Record<string, string | number>) {
  if (!params) {
    return template;
  }

  return template.replace(/\{(\w+)\}/g, (_, key: string) => String(params[key] ?? ""));
}

export function useI18n() {
  const locale = computed(() => currentLocale.value);

  function t(path: string, params?: Record<string, string | number>) {
    const localized = resolvePath(messages[currentLocale.value], path)
      ?? resolvePath(messages.cs, path)
      ?? path;
    return interpolate(localized, params);
  }

  function setLocale(nextLocale: Locale) {
    currentLocale.value = nextLocale;
    if (typeof document !== "undefined") {
      document.documentElement.lang = nextLocale;
    }
  }

  return {
    locale,
    setLocale,
    t,
  };
}
