"""Non-English UI packs must differ from en.json (not overlay-only English)."""

from __future__ import annotations

import json
from pathlib import Path

LOCALES = Path(__file__).resolve().parents[1] / "frontend" / "src" / "locales"


def _load(name: str) -> dict:
    return json.loads((LOCALES / name).read_text(encoding="utf-8"))


def _flat_strings(node: object, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    if isinstance(node, dict):
        for key, val in node.items():
            path = f"{prefix}.{key}" if prefix else key
            out.update(_flat_strings(val, path))
    elif isinstance(node, str):
        out[prefix] = node
    return out


def test_french_pack_translates_core_navigation_and_assistant():
    en = _flat_strings(_load("en.json"))
    fr = _flat_strings(_load("fr.json"))
    must_differ = (
        "assistant.title",
        "assistant.lede.desktop",
        "assistant.tabs.retention",
        "nav.business.title",
        "nav.customer.title",
    )
    for key in must_differ:
        assert key in fr, key
        assert fr[key] != en[key], f"{key} still English: {fr[key]!r}"
    # "Conversation" is valid in French (same spelling as English).
    assert fr["assistant.tabs.conversation"] in ("Conversation", "Discussions")


def test_french_pack_mostly_translated_not_copy_of_english():
    en = _flat_strings(_load("en.json"))
    fr = _flat_strings(_load("fr.json"))
    same = sum(1 for k, v in en.items() if fr.get(k) == v)
    assert same / len(en) < 0.15, f"fr.json is {100 * same / len(en):.1f}% identical to en"
