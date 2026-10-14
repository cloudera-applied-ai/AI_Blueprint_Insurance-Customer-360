"""Default initialization region is UK (gb) with English seed language."""

from __future__ import annotations

from pathlib import Path
import sqlite3

import pytest

from customer360.seed import init_database
from customer360.territory import DEFAULT_TERRITORY_ID, resolve_territory_id
from customer360.territory.languages import resolve_seed_language
from customer360.territory_store import load_territory_config


def test_resolve_territory_defaults_to_gb(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CUSTOMER360_SEED_TERRITORY", raising=False)
    monkeypatch.delenv("CUSTOMER360_TERRITORY", raising=False)
    assert DEFAULT_TERRITORY_ID == "gb"
    assert resolve_territory_id() == "gb"


def test_resolve_seed_language_defaults_to_en(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CUSTOMER360_SEED_LANGUAGE", raising=False)
    assert resolve_seed_language() == "en"


def test_init_database_default_region_and_language(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CUSTOMER360_SEED_SKIP_LLM", "1")
    monkeypatch.delenv("CUSTOMER360_SEED_TERRITORY", raising=False)
    monkeypatch.delenv("CUSTOMER360_SEED_LANGUAGE", raising=False)
    db = tmp_path / "default.db"
    init_database(db, rebuild=True, customer_count=15)
    with sqlite3.connect(db) as conn:
        cfg = load_territory_config(conn)
    assert cfg is not None
    assert cfg["territory_id"] == "gb"
    assert cfg["seed_language"] == "en"
    assert cfg["currency"] == "GBP"
