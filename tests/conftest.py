"""Shared pytest fixtures for Customer 360 integration tests."""

from __future__ import annotations

import os
import sqlite3

import pytest

from customer360.seed import init_database


@pytest.fixture(scope="session")
def warehouse_db_path(tmp_path_factory: pytest.TempPathFactory) -> str:
    """Seed a small warehouse once per test session (isolated from dev data/customer360.db)."""
    db = tmp_path_factory.mktemp("warehouse") / "customer360.db"
    path = str(db)
    os.environ["CUSTOMER360_DB_PATH"] = path
    os.environ["CUSTOMER360_SEED_SKIP_LLM"] = "1"
    init_database(db, rebuild=True, customer_count=80, territory_id="gb", seed_language="en")
    from customer360.api.customer_list import reset_known_cities_cache
    from customer360.churn.scoring import try_train_and_score_churn

    reset_known_cities_cache()
    try_train_and_score_churn(db)
    return path


@pytest.fixture(scope="session", autouse=True)
def _bind_test_warehouse(warehouse_db_path: str) -> None:
    """Ensure default_db_path() resolves to the session warehouse for all tests."""
    os.environ["CUSTOMER360_DB_PATH"] = warehouse_db_path


@pytest.fixture
def conn(warehouse_db_path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(warehouse_db_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()
