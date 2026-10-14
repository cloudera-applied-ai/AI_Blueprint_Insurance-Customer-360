"""Rebuild the SQLite warehouse with a chosen region and seed language."""

from __future__ import annotations

from pathlib import Path

from customer360.data_source import ensure_sqlite_warehouse_path_registered, resolve_sqlite_warehouse_path
from customer360.seed import DEFAULT_SEED_CUSTOMERS, MAX_SEED_CUSTOMERS, init_database
from customer360.territory import get_territory
from customer360.territory.languages import get_language, resolve_seed_language


def reseed_warehouse(
    *,
    territory_id: str,
    seed_language: str,
    customer_count: int | None = None,
    db_path: Path | None = None,
) -> dict[str, str | int]:
    """Delete and recreate the warehouse at the configured path."""
    from customer360.api.customer_list import reset_known_cities_cache

    tid = get_territory(territory_id).id
    lang = get_language(seed_language)
    path = (db_path or resolve_sqlite_warehouse_path()).resolve()
    raw_count = customer_count if customer_count is not None else DEFAULT_SEED_CUSTOMERS
    n = max(1, min(int(raw_count), MAX_SEED_CUSTOMERS))

    init_database(
        path,
        rebuild=True,
        customer_count=n,
        territory_id=tid,
        seed_language=lang,
    )
    ensure_sqlite_warehouse_path_registered(path)
    reset_known_cities_cache()
    return {
        "db_path": str(path),
        "territory_id": tid,
        "seed_language": lang,
        "customer_count": n,
    }
