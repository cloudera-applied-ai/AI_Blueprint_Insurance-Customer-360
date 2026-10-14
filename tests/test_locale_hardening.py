"""Guardrails: no Hebrew or fixed currency glyphs in UI source (use i18n + Intl)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SRC = ROOT / "frontend" / "src"

HEBREW = re.compile(r"[\u0590-\u05FF]")
SHEKEL = "₪"
HARDCODED_ILS = re.compile(r"\bILS\b")

SCAN_SUFFIXES = {".ts", ".tsx", ".css"}
SKIP_DIRS = {"locales", "dist"}


def _iter_frontend_sources():
    for path in FRONTEND_SRC.rglob("*"):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def test_no_hebrew_characters_in_frontend_source():
    offenders: list[str] = []
    for path in _iter_frontend_sources():
        text = path.read_text(encoding="utf-8")
        if HEBREW.search(text):
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, "Hebrew must live in locale JSON only: " + ", ".join(offenders)


def test_no_shekel_glyph_in_frontend_source():
    offenders: list[str] = []
    for path in _iter_frontend_sources():
        text = path.read_text(encoding="utf-8")
        if SHEKEL in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, "Use formatMoney/formatMoneyZero instead of ₪ in: " + ", ".join(offenders)


def test_no_hardcoded_ils_in_frontend_ts():
    offenders: list[str] = []
    for path in _iter_frontend_sources():
        if path.suffix not in {".ts", ".tsx"}:
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if HARDCODED_ILS.search(line) and "currency" not in line.lower():
                offenders.append(f"{path.relative_to(ROOT)}:{i}")
    assert not offenders, "Avoid hardcoded ILS in UI source: " + ", ".join(offenders)
