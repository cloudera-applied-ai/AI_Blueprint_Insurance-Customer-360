"""Insight and retention prompts honor client UI locale."""

from __future__ import annotations

from customer360.agent.locale import insight_language_instruction
from customer360.insights.prompt import build_insight_system_prompt, build_user_prompt


def test_insight_prompts_include_french_when_locale_fr():
    system = build_insight_system_prompt("fr", market_context="UK insurance")
    user = build_user_prompt({"customer_name": "Alex"}, "HIGH", locale="fr")
    assert "French" in system
    assert "ui_locale=fr" in user or "French" in user


def test_retention_stream_builds_arabic_instruction():
    system = insight_language_instruction("ar", market_context="European market")
    assert "Arabic" in system
    assert "Never respond in French" in system


def test_insight_user_prompt_includes_locale_es():
    user = build_user_prompt({"customer_name": "Alex"}, "MEDIUM", locale="es")
    assert "ui_locale=es" in user or "Spanish" in user

