import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "../locales/en.json";
import he from "../locales/he.json";
import fr from "../locales/fr.json";
import es from "../locales/es.json";
import ar from "../locales/ar.json";
import { getTerritoryFormatting } from "../territoryConfig";

export const LOCALE_STORAGE_KEY = "customer360.locale";

export type ApiLocaleCode = "en" | "fr" | "he" | "es" | "ar";

function applyDocumentLanguage(lng: string) {
  const root = document.documentElement;
  const code = lng.split("-")[0];
  const rtl = code === "he" || code === "ar";
  root.lang = code;
  root.dir = rtl ? "rtl" : "ltr";
}

function normalizeStoredLocale(raw: string | null, supported: string[]): ApiLocaleCode {
  let code = (raw || "").split("-")[0].toLowerCase();
  if (code === "il") code = "he";
  if (code === "fr" && supported.includes("fr")) return "fr";
  if (code === "he" && supported.includes("he")) return "he";
  if (code === "es" && supported.includes("es")) return "es";
  if (code === "ar" && supported.includes("ar")) return "ar";
  return "en";
}

const saved =
  typeof localStorage !== "undefined"
    ? localStorage.getItem(LOCALE_STORAGE_KEY)
    : null;
const initialSupported = getTerritoryFormatting().supported_ui_locales;
const initial = normalizeStoredLocale(saved, initialSupported);

void i18n.use(initReactI18next).init({
  supportedLngs: ["en", "fr", "es", "he", "ar"],
  nonExplicitSupportedLngs: true,
  resources: {
    en: { translation: en },
    he: { translation: he },
    fr: { translation: fr },
    es: { translation: es },
    ar: { translation: ar },
  },
  lng: initial,
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

applyDocumentLanguage(i18n.language);

i18n.on("languageChanged", (lng) => {
  applyDocumentLanguage(lng);
  void import("../localeFormat").then(({ resetLocaleFormatters }) => resetLocaleFormatters());
  try {
    const code = apiLocaleCode();
    localStorage.setItem(LOCALE_STORAGE_KEY, code);
  } catch {
    /* private mode */
  }
});

export default i18n;

/** Locale code sent to the API for LLM prompts. */
export function apiLocaleCode(): ApiLocaleCode {
  const lng = i18n.language || "en";
  if (lng.startsWith("he")) return "he";
  if (lng.startsWith("fr")) return "fr";
  if (lng.startsWith("es")) return "es";
  if (lng.startsWith("ar")) return "ar";
  return "en";
}

/** Active UI locale key. */
export function uiLocaleCode(): ApiLocaleCode {
  const lng = i18n.language || "en";
  if (lng.startsWith("he")) return "he";
  if (lng.startsWith("fr")) return "fr";
  if (lng.startsWith("es")) return "es";
  if (lng.startsWith("ar")) return "ar";
  return "en";
}

/** BCP 47 locale for Intl (currency/numbers), aligned with UI language and territory. */
export function appIntlLocale(): string {
  const ui = uiLocaleCode();
  const territory = getTerritoryFormatting().intl_locale;
  const region = territory.includes("-") ? territory.split("-")[1] : "US";
  if (ui === "he") return `he-${region}`;
  if (ui === "fr") return territory.startsWith("fr") ? territory : `fr-${region}`;
  if (ui === "es") return territory.startsWith("es") ? territory : `es-${region}`;
  if (ui === "ar") return territory.startsWith("ar") ? territory : `ar-${region}`;
  if (territory.startsWith("en")) return territory;
  return `en-${region}`;
}

export function syncI18nWithTerritory(supported: string[], _primary: string): void {
  const allowed = supported.length ? supported : ["en"];
  const stored =
    typeof localStorage !== "undefined"
      ? localStorage.getItem(LOCALE_STORAGE_KEY)
      : null;
  const active = normalizeStoredLocale(i18n.resolvedLanguage || i18n.language, allowed);
  let next = normalizeStoredLocale(stored, allowed);
  if (!stored && allowed.includes(active)) {
    next = active;
  } else if (!stored && allowed.includes("en")) {
    next = "en";
  }
  if (!allowed.includes(next)) {
    const primaryCode = _primary.split("-")[0];
    next = normalizeStoredLocale(primaryCode, allowed);
  }
  if (!allowed.includes(next)) {
    next = normalizeStoredLocale(allowed[0] ?? "en", allowed);
  }
  if (i18n.language !== next) {
    void i18n.changeLanguage(next);
  }
}
