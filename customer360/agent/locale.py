"""UI locale hints for assistant responses."""

from __future__ import annotations

import sqlite3

SUPPORTED_UI_LOCALES = frozenset({"en", "fr", "he", "es", "ar"})

LANGUAGE_NAMES = {
    "en": "English",
    "fr": "French",
    "he": "Modern Hebrew",
    "es": "Spanish",
    "ar": "Modern Standard Arabic",
}


def normalize_ui_locale(locale: str | None) -> str:
    raw = (locale or "").strip().lower().replace("_", "-")
    if raw.startswith("il"):
        return "he"
    if raw.startswith("he"):
        return "he"
    if raw.startswith("fr"):
        return "fr"
    if raw.startswith("es"):
        return "es"
    if raw.startswith("ar"):
        return "ar"
    if raw.startswith("en"):
        return "en"
    return "en"


def resolve_llm_locale(
    client_locale: str | None,
    conn: sqlite3.Connection | None = None,
) -> str:
    """Resolve LLM response language from the client UI locale; default English."""
    del conn
    if client_locale and str(client_locale).strip():
        return normalize_ui_locale(client_locale)
    return "en"


def _market_context_suffix(market_context: str | None) -> str:
    if not market_context or not market_context.strip():
        return ""
    return (
        f"\nMarket/regulatory context (for product terminology only — do NOT switch response "
        f"language because of this): {market_context.strip()}."
    )


def _language_lock(code: str) -> str:
    lang = LANGUAGE_NAMES.get(code, "English")
    if code == "en":
        return ""
    return (
        f"\nCRITICAL: Respond only in {lang}. Do not use French, English, or any other language "
        f"for user-facing JSON string values unless ui_locale is explicitly {code}."
    )


def bedrock_language_instruction(
    locale: str | None,
    *,
    market_context: str | None = None,
) -> str:
    code = normalize_ui_locale(locale)
    market = _market_context_suffix(market_context)
    lock = _language_lock(code)
    if code == "he":
        return f"""
Language (required): The user's application UI is set to Hebrew (he-IL).
Write the JSON "answer" field entirely in Modern Hebrew with a professional insurance tone.{market}{lock}
Keep JSON property names, action_ids, segment keys, and API/tool identifiers in English as required.
Do not answer in English except for untranslatable proper nouns, codes, or numbers from live data.
If the user writes in Hebrew, match their language. If they write in English but UI is Hebrew, still respond in Hebrew.
"""
    if code == "fr":
        return f"""
Language (required): The user's application UI is set to French (fr).
Write the JSON "answer" field entirely in French with a professional insurance tone.{market}{lock}
Keep JSON property names, action_ids, segment keys, and API/tool identifiers in English as required.
Use live data numbers and proper nouns as provided.
"""
    if code == "es":
        return f"""
Language (required): The user's application UI is set to Spanish (es).
Write the JSON "answer" field entirely in Spanish with a professional insurance tone.{market}{lock}
Keep JSON property names, action_ids, segment keys, and API/tool identifiers in English as required.
Use live data numbers and proper nouns as provided.
"""
    if code == "ar":
        return f"""
Language (required): The user's application UI is set to Arabic (ar-SA).
Write the JSON "answer" field entirely in Modern Standard Arabic with a professional insurance tone.{market}{lock}
Keep JSON property names, action_ids, segment keys, and API/tool identifiers in English as required.
Use live data numbers and proper nouns as provided.
Never respond in French even if market context describes a French or European market.
"""
    return f"""
Language: The user's application UI is set to English. Write the JSON "answer" field in English unless the user clearly asks for another language.{market}
"""


def insight_language_instruction(
    locale: str | None,
    *,
    market_context: str | None = None,
) -> str:
    code = normalize_ui_locale(locale)
    market = _market_context_suffix(market_context)
    lock = _language_lock(code)
    if code == "he":
        return f"""
Language (required): The application UI is Hebrew (he-IL).
Write every JSON string value (preamble, summary, guidance, each suggested_actions entry,
experience_note) in Modern Hebrew with a professional insurance tone.{market}{lock}
Keep JSON keys and primary_focus values ("upsell" / "retention") in English.
If live data is in English, you may keep proper nouns and codes as-is inside Hebrew prose.
"""
    if code == "fr":
        return f"""
Language (required): The application UI is French (fr).
Write every JSON string value in French with a professional insurance tone.{market}{lock}
Keep JSON keys and primary_focus values in English.
"""
    if code == "es":
        return f"""
Language (required): The application UI is Spanish (es).
Write every JSON string value in Spanish with a professional insurance tone.{market}{lock}
Keep JSON keys and primary_focus values in English.
"""
    if code == "ar":
        return f"""
Language (required): The application UI is Arabic (ar-SA).
Write every JSON string value in Modern Standard Arabic with a professional insurance tone.{market}{lock}
Keep JSON keys and primary_focus values in English.
Never respond in French even if market context describes a French or European market.
"""
    return f"""
Language: The application UI is English. Write all JSON string values in English unless the
user data clearly requires another language for customer-facing phrases.{market}
"""


def draft_language_instruction(
    locale: str | None,
    *,
    market_context: str | None = None,
) -> str:
    code = normalize_ui_locale(locale)
    market = _market_context_suffix(market_context)
    lock = _language_lock(code)
    if code == "he":
        return f"""
Language (required): The application UI is Hebrew (he-IL).
Write subject and body in Modern Hebrew (professional Customer Care tone).{market}{lock}
Keep JSON keys and channel value in English. SMS may include the portal URL as given in the rules.
"""
    if code == "fr":
        return f"""
Language (required): The application UI is French (fr).
Write subject and body in French (professional Customer Care tone).{market}{lock}
Keep JSON keys and channel value in English.
"""
    if code == "es":
        return f"""
Language (required): The application UI is Spanish (es).
Write subject and body in Spanish (professional Customer Care tone).{market}{lock}
Keep JSON keys and channel value in English.
"""
    if code == "ar":
        return f"""
Language (required): The application UI is Arabic (ar-SA).
Write subject and body in Modern Standard Arabic (professional Customer Care tone).{market}{lock}
Keep JSON keys and channel value in English.
Never respond in French even if market context describes a French or European market.
"""
    return f"""
Language: The application UI is English. Write subject and body in English unless the customer
context clearly requires another language.{market}
"""
