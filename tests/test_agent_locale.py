"""LLM locale resolution and prompt language locks."""

from __future__ import annotations

from customer360.agent.locale import (
    bedrock_language_instruction,
    normalize_ui_locale,
    resolve_llm_locale,
)


def test_normalize_ui_locale_maps_il_to_hebrew():
    assert normalize_ui_locale("il") == "he"
    assert normalize_ui_locale("he-IL") == "he"
    assert normalize_ui_locale("ar-SA") == "ar"
    assert normalize_ui_locale("fr-FR") == "fr"


def test_resolve_llm_locale_prefers_client_and_defaults_english():
    assert resolve_llm_locale("ar", object()) == "ar"
    assert resolve_llm_locale(None, object()) == "en"
    assert resolve_llm_locale("", object()) == "en"


def test_arabic_instruction_resists_french_market_context():
    text = bedrock_language_instruction(
        "ar",
        market_context="French insurance and European regulatory context",
    )
    assert "Modern Standard Arabic" in text
    assert "Never respond in French" in text
    assert "for product terminology only" in text
