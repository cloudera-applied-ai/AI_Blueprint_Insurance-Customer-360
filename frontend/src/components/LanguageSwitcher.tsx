import { useTranslation } from "react-i18next";
import { useTerritory } from "../territoryContext";
import { uiLocaleCode } from "../i18n/index";

/** Visible header labels — always short codes (never territory-qualified API labels). */
const SHORT_UI_LABEL: Record<string, string> = {
  en: "En",
  fr: "Fr",
  he: "He",
  es: "Es",
  ar: "Ar",
};

const FULL_LANGUAGE_NAMES: Record<string, string> = {
  en: "English",
  fr: "French",
  he: "Hebrew",
  es: "Spanish",
  ar: "Arabic",
};

export default function LanguageSwitcher() {
  const { i18n, t } = useTranslation();
  const { context } = useTerritory();
  const current = uiLocaleCode();

  const codes = context.supported_ui_locales?.length
    ? context.supported_ui_locales
    : ["en", "fr", "es", "he", "ar"];

  const options = codes
    .filter((code) => SHORT_UI_LABEL[code])
    .map((code) => ({
      code,
      short: SHORT_UI_LABEL[code],
      full: FULL_LANGUAGE_NAMES[code] ?? code,
    }));

  if (options.length <= 1) {
    return null;
  }

  return (
    <div className="lang-switcher" role="group" aria-label={t("app.language")}>
      {options.map(({ code, short, full }) => (
        <button
          key={code}
          type="button"
          className={`lang-switcher-btn${current === code ? " is-active" : ""}`}
          onClick={() => void i18n.changeLanguage(code)}
          aria-pressed={current === code}
          aria-label={full}
          title={full}
        >
          {short}
        </button>
      ))}
    </div>
  );
}
