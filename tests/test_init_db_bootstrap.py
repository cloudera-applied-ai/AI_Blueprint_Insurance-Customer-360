"""First-time warehouse init when the SQLite file does not exist yet."""

from __future__ import annotations

from pathlib import Path

import pytest

from customer360.data_source import load_data_source_config, resolve_sqlite_warehouse_path
from customer360.db import connect
from customer360.seed import init_database


def test_init_creates_configured_cdsw_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    warehouse = tmp_path / "data" / "customer360.db"
    monkeypatch.setenv("CUSTOMER360_DB_PATH", str(warehouse))
    monkeypatch.setenv("CUSTOMER360_SEED_SKIP_LLM", "1")
    assert not warehouse.is_file()

    init_database(warehouse, rebuild=True, customer_count=10, territory_id="gb", seed_language="en")

    assert warehouse.is_file()
    assert resolve_sqlite_warehouse_path() == warehouse.resolve()
    cfg = load_data_source_config()
    assert Path(cfg.sqlite_path or "").resolve() == warehouse.resolve()
    conn = connect(warehouse)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM DWH_DIM_CUSTOMERS_UNIQUE WHERE CURRENT_IND = 1"
        ).fetchone()[0]
        assert count == 10
    finally:
        conn.close()
