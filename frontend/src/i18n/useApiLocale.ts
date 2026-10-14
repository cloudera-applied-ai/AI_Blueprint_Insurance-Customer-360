import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import type { ApiLocaleCode } from "./index";

function localeFromI18n(lng: string): ApiLocaleCode {
  if (lng.startsWith("he")) return "he";
  if (lng.startsWith("fr")) return "fr";
  if (lng.startsWith("es")) return "es";
  if (lng.startsWith("ar")) return "ar";
  return "en";
}

/** Reactive UI locale for API / LLM calls (updates when the language switcher changes). */
export function useApiLocale(): ApiLocaleCode {
  const { i18n } = useTranslation();
  const lng = i18n.resolvedLanguage || i18n.language || "en";
  return useMemo(() => localeFromI18n(lng), [lng]);
}
