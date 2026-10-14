"""Territory-aware warehouse seeding."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from customer360.api.customer_list import normalize_city_name, reset_known_cities_cache
from customer360.seed import init_database
from customer360.territory import get_territory
from customer360.territory_store import load_territory_config


@pytest.mark.parametrize(
    ("territory_id", "expected_city", "email_suffix"),
    [
        ("il", "Tel Aviv", "example.co.il"),
        ("gb", "London", "example.co.uk"),
        ("es", "Madrid", "ejemplo.es"),
        ("sa", "Riyadh", "example.sa"),
        ("fr", "Paris", "exemple.fr"),
    ],
)
def test_seed_territory_profiles(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    territory_id: str,
    expected_city: str,
    email_suffix: str,
) -> None:
    db = tmp_path / f"{territory_id}.db"
    init_database(db, rebuild=True, customer_count=40, territory_id=territory_id)
    monkeypatch.setenv("CUSTOMER360_DB_PATH", str(db))
    reset_known_cities_cache()

    with sqlite3.connect(db) as conn:
        cfg = load_territory_config(conn)
        assert cfg is not None
        assert cfg["territory_id"] == territory_id
        assert cfg["currency"] == get_territory(territory_id).default_currency

        row = conn.execute(
            "SELECT CITY_NAME, EMAIL FROM DWH_DIM_CUSTOMERS_UNIQUE WHERE CURRENT_IND = 1 LIMIT 1"
        ).fetchone()
        assert row is not None
        assert row[0] in get_territory(territory_id).canonical_cities()
        assert str(row[1]).endswith(f"@{email_suffix}")

    aliases = get_territory(territory_id).known_cities_map()
    assert aliases[expected_city.lower()] == expected_city
    assert normalize_city_name(expected_city.lower()) == expected_city
