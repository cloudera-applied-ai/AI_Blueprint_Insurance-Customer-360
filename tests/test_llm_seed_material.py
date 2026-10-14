"""LLM-backed seed material resolution."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from customer360.seed import init_database
from customer360.seed_material import material_from_profile, material_to_dict, resolve_seed_material
from customer360.territory import get_territory
from customer360.territory_store import load_territory_config


def test_resolve_seed_material_uses_profile_when_skip_llm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CUSTOMER360_SEED_SKIP_LLM", "1")
    profile = get_territory("il")
    material = resolve_seed_material(profile, "en")
    assert material.source == "profile"
    assert material.territory_id == "il"
    assert material.seed_language == "en"
    assert material.first_names == profile.first_names


def test_init_database_with_mock_llm_material(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CUSTOMER360_SEED_SKIP_LLM", raising=False)
    profile = get_territory("gb")
    base = material_from_profile(profile, "en", source="profile")
    payload = material_to_dict(base)
    payload["first_names"] = ["LLMGenerated"] + list(payload["first_names"][1:])

    def fake_invoke(*, system_prompt: str, user_prompt: str, json_mode: bool = False):
        return json.dumps(payload), "mock-model"

    monkeypatch.setattr("customer360.llm.router.is_llm_configured", lambda: True)
    monkeypatch.setattr("customer360.llm.router.invoke_text", fake_invoke)

    db = tmp_path / "llm.db"
    init_database(db, rebuild=True, customer_count=12, territory_id="gb", seed_language="en")

    with sqlite3.connect(db) as conn:
        cfg = load_territory_config(conn)
        assert cfg is not None
        assert cfg.get("seed_material_source") == "llm"
        row = conn.execute(
            "SELECT FIRST_NAME FROM DWH_DIM_CUSTOMERS_UNIQUE WHERE CURRENT_IND = 1 LIMIT 1"
        ).fetchone()
        assert row is not None
        assert row[0] == "LLMGenerated"
