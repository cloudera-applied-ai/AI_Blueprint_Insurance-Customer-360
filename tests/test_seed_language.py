"""Seed language is independent of geographic region."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from customer360.seed import init_database
from customer360.territory_store import load_territory_config
from customer360.warehouse_reseed import reseed_warehouse


def test_israel_region_english_interaction_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CUSTOMER360_SEED_SKIP_LLM", "1")
    db = tmp_path / "il-en.db"
    init_database(
        db,
        rebuild=True,
        customer_count=25,
        territory_id="il",
        seed_language="en",
    )
    with sqlite3.connect(db) as conn:
        cfg = load_territory_config(conn)
        assert cfg is not None
        assert cfg["territory_id"] == "il"
        assert cfg["seed_language"] == "en"
        sample = conn.execute(
            "SELECT QUERY_OR_TITLE FROM APP_CUSTOMER_INTERACTION_EVENTS LIMIT 5"
        ).fetchall()
    titles = " ".join(row[0] for row in sample)
    assert "Premium" in titles or "payment" in titles.lower() or "pension" in titles.lower()


def test_israel_region_hebrew_interaction_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CUSTOMER360_SEED_SKIP_LLM", "1")
    db = tmp_path / "il-he.db"
    init_database(
        db,
        rebuild=True,
        customer_count=25,
        territory_id="il",
        seed_language="he",
    )
    with sqlite3.connect(db) as conn:
        cfg = load_territory_config(conn)
        assert cfg["seed_language"] == "he"
        sample = conn.execute(
            "SELECT QUERY_OR_TITLE FROM APP_CUSTOMER_INTERACTION_EVENTS LIMIT 5"
        ).fetchall()
    titles = " ".join(row[0] for row in sample)
    assert any("\u0590" <= ch <= "\u05ff" for ch in titles)


def test_reseed_warehouse(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "reseed.db"
    monkeypatch.setenv("CUSTOMER360_DB_PATH", str(db))
    monkeypatch.setenv("CUSTOMER360_SEED_SKIP_LLM", "1")
    result = reseed_warehouse(territory_id="fr", seed_language="fr", customer_count=30)
    assert result["territory_id"] == "fr"
    assert result["seed_language"] == "fr"
    assert result["customer_count"] == 30
    assert db.is_file()
    with sqlite3.connect(db) as conn:
        cfg = load_territory_config(conn)
        assert cfg["territory_id"] == "fr"
        assert cfg["seed_language"] == "fr"
