"""Reseed must target the admin-configured warehouse SQLite path."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from customer360.admin_store import ensure_admin_schema
from customer360.data_source import load_data_source_config, save_data_source_config, DataSourceConfig
from customer360.db import connect
from customer360.seed import init_database
from customer360.warehouse_reseed import reseed_warehouse


def test_reseed_uses_admin_sqlite_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bootstrap = tmp_path / "control.db"
    warehouse = tmp_path / "nested" / "customer360.db"
    warehouse.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("CUSTOMER360_DB_PATH", str(bootstrap))
    monkeypatch.setenv("CUSTOMER360_SEED_SKIP_LLM", "1")

    conn = sqlite3.connect(bootstrap)
    ensure_admin_schema(conn)
    conn.commit()
    conn.close()

    save_data_source_config(
        DataSourceConfig(
            backend_type="sqlite",
            sqlite_path=str(warehouse),
        )
    )

    reseed_warehouse(territory_id="gb", seed_language="en", customer_count=15)

    assert warehouse.is_file()
    cfg = load_data_source_config()
    assert Path(cfg.sqlite_path or "").resolve() == warehouse.resolve()

    wh_conn = connect(warehouse)
    try:
        count = wh_conn.execute(
            "SELECT COUNT(*) FROM DWH_DIM_CUSTOMERS_UNIQUE WHERE CURRENT_IND = 1"
        ).fetchone()[0]
        assert count == 15
    finally:
        wh_conn.close()
