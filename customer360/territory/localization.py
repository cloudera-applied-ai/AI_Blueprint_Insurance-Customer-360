"""UI localization options per territory (language + region)."""

from __future__ import annotations

from customer360.territory.languages import LANGUAGE_LABELS, UI_LANGUAGE_IDS
from customer360.territory.models import TerritoryProfile


def _region_from_intl(intl_locale: str) -> str:
    if "-" in intl_locale:
        return intl_locale.split("-", 1)[1]
    return intl_locale.upper()


def _bcp47_for_language(language_code: str, profile: TerritoryProfile) -> str:
    region = _region_from_intl(profile.default_intl_locale)
    if language_code == "en":
        return profile.default_intl_locale if profile.default_intl_locale.startswith("en") else f"en-{region}"
    if language_code == "fr":
        return profile.default_intl_locale if profile.default_intl_locale.startswith("fr") else f"fr-{region}"
    if language_code == "es":
        return profile.default_intl_locale if profile.default_intl_locale.startswith("es") else f"es-{region}"
    if language_code == "he":
        return f"he-{region}"
    if language_code == "ar":
        return profile.default_intl_locale if profile.default_intl_locale.startswith("ar") else f"ar-{region}"
    return profile.default_intl_locale


def localization_options(profile: TerritoryProfile) -> list[dict[str, str]]:
    """Human-facing localization choices for the active territory."""
    options: list[dict[str, str]] = []
    for code in UI_LANGUAGE_IDS:
        label = LANGUAGE_LABELS[code]
        if code == "en" and profile.id != "gb":
            label = f"{label} ({profile.display_name})"
        elif code == "he" and profile.id == "il":
            label = f"{label} ({profile.display_name})"
        options.append(
            {
                "code": code,
                "language_code": code,
                "label": label,
                "bcp47": _bcp47_for_language(code, profile),
                "territory_id": profile.id,
            }
        )
    return options


def territory_catalog_entry(profile: TerritoryProfile) -> dict:
    return {
        "territory_id": profile.id,
        "display_name": profile.display_name,
        "currency": profile.default_currency,
        "primary_ui_locale": profile.primary_ui_locale,
        "supported_ui_locales": list(UI_LANGUAGE_IDS),
        "default_seed_language": profile.default_seed_language,
        "localizations": localization_options(profile),
        "llm_market_context": profile.llm_market_context,
    }
