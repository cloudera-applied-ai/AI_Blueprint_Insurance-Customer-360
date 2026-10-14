"""Admin-persisted localization preferences."""

from __future__ import annotations

import sqlite3

from customer360.localization_admin import (
    LocalizationAdminConfig,
    load_localization_admin,
    save_localization_admin,
)
from customer360.territory_runtime import territory_payload


def test_save_and_apply_localization_admin(tmp_path, monkeypatch) -> None:
    db = tmp_path / "wh.db"
    monkeypatch.setenv("CUSTOMER360_DB_PATH", str(db))

    from customer360.seed import init_database

    init_database(db, rebuild=True, customer_count=20, territory_id="il")

    save_localization_admin(
        LocalizationAdminConfig(territory_id="es", ui_locale="es"),
    )
    loaded = load_localization_admin()
    assert loaded.territory_id == "es"
    assert loaded.ui_locale == "es"

    with sqlite3.connect(db) as conn:
        payload = territory_payload(conn)
    assert payload["territory_id"] == "es"
    assert payload["currency"] == "EUR"
    assert payload["preferred_ui_locale"] == "es"
    assert payload["warehouse_territory_id"] == "il"
    assert payload["territory_mismatch"] is True


def test_supported_ui_locales_persist_and_flow_to_app_context(tmp_path, monkeypatch) -> None:
    db = tmp_path / "wh.db"
    monkeypatch.setenv("CUSTOMER360_DB_PATH", str(db))

    from customer360.seed import init_database

    init_database(db, rebuild=True, customer_count=20, territory_id="gb")

    save_localization_admin(
        LocalizationAdminConfig(
            supported_ui_locales=["en", "he"],
            ui_locale="en",
        ),
    )
    loaded = load_localization_admin()
    assert loaded.normalized_supported_ui_locales() == ["en", "he"]

    with sqlite3.connect(db) as conn:
        payload = territory_payload(conn)
    assert payload["supported_ui_locales"] == ["en", "he"]
    assert "fr" not in payload["supported_ui_locales"]
