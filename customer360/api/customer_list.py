"""Shared WHERE clause builder for customer list / copilot queries."""

from __future__ import annotations

from customer360.api.segments import normalize_segment, segment_scope_sql

VALID_CHURN_RISK_TIERS = frozenset({"HIGH", "MEDIUM", "LOW"})

_known_cities_cache: dict[str, str] | None = None


def known_cities_map() -> dict[str, str]:
    global _known_cities_cache
    if _known_cities_cache is not None:
        return _known_cities_cache
    try:
        import sqlite3

        from customer360.data_source import resolve_sqlite_warehouse_path
        from customer360.territory import get_territory
        from customer360.territory_store import load_territory_config

        db_path = resolve_sqlite_warehouse_path()
        if db_path.is_file() and db_path.stat().st_size > 0:
            with sqlite3.connect(db_path) as conn:
                cfg = load_territory_config(conn)
                if cfg and cfg.get("territory_id"):
                    _known_cities_cache = get_territory(str(cfg["territory_id"])).known_cities_map()
                    return _known_cities_cache
    except (OSError, ValueError, KeyError):
        pass
    from customer360.territory import get_territory, resolve_territory_id

    _known_cities_cache = get_territory(resolve_territory_id()).known_cities_map()
    return _known_cities_cache


def reset_known_cities_cache() -> None:
    global _known_cities_cache
    _known_cities_cache = None


def normalize_city_name(raw: str | None) -> str | None:
    if not raw or not str(raw).strip():
        return None
    text = str(raw).strip()
    cities = known_cities_map()
    key = text.lower()
    if key in cities:
        return cities[key]
    for alias, canonical in cities.items():
        if alias in key or key in alias:
            return canonical
    return text if len(text) >= 2 else None


def normalize_churn_risk_tier(raw: str | None) -> str | None:
    if raw is None or not str(raw).strip():
        return None
    text = str(raw).strip().upper()
    if text in VALID_CHURN_RISK_TIERS:
        return text
    lowered = str(raw).strip().lower()
    if "high" in lowered:
        return "HIGH"
    if "medium" in lowered or "med" in lowered:
        return "MEDIUM"
    if "low" in lowered:
        return "LOW"
    return None


def customer_list_where(
    seg: str,
    q: str | None,
    policy_type_code: int | None = None,
    city: str | None = None,
    churn_risk_tier: str | None = None,
) -> tuple[str, list[object]]:
    where, params = segment_scope_sql(normalize_segment(seg))
    if q and q.strip():
        where += " AND (c.CUSTOMER_NAME LIKE ? OR CAST(c.CUSTOMER_ID AS TEXT) LIKE ?)"
        like = f"%{q.strip()}%"
        params.extend([like, like])
    city_canon = normalize_city_name(city)
    if city_canon:
        where += " AND c.CITY_NAME = ?"
        params.append(city_canon)
    if policy_type_code is not None:
        where += """
            AND EXISTS (
                SELECT 1 FROM DWH_DIM_ALL_POLICY p
                WHERE p.CUSTOMER_ID = CAST(c.CUSTOMER_ID AS TEXT)
                  AND p.POLICY_TYPE_CODE = ?
            )
        """
        params.append(int(policy_type_code))
    tier = normalize_churn_risk_tier(churn_risk_tier)
    if tier:
        where += """
            AND EXISTS (
                SELECT 1 FROM APP_CUSTOMER_CHURN_SCORES ch
                WHERE ch.CUSTOMER_ID = c.CUSTOMER_ID
                  AND UPPER(ch.CHURN_RISK_TIER) = ?
            )
        """
        params.append(tier)
    return where, params
