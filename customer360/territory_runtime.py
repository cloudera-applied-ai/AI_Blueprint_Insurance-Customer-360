"""Runtime territory settings (warehouse seed + admin overrides)."""

from __future__ import annotations

import sqlite3

from customer360.localization_admin import load_localization_admin, resolve_supported_ui_locales
from customer360.territory import get_territory, resolve_territory_id
from customer360.territory.localization import localization_options
from customer360.territory_store import default_territory_payload, load_territory_config


def _profile_payload(profile, *, warehouse: dict | None) -> dict:
    cities = list(profile.canonical_cities())
    city_aliases = profile.known_cities_map()
    if warehouse:
        if warehouse.get("cities"):
            cities = list(warehouse["cities"])
        if warehouse.get("city_aliases"):
            city_aliases = dict(warehouse["city_aliases"])
    return {
        "territory_id": profile.id,
        "display_name": profile.display_name,
        "currency": profile.default_currency,
        "intl_locale": profile.default_intl_locale,
        "primary_ui_locale": profile.primary_ui_locale,
        "supported_ui_locales": resolve_supported_ui_locales(),
        "cities": cities,
        "city_aliases": city_aliases,
        "llm_market_context": profile.llm_market_context,
        "portal_sms_url_template": profile.portal_sms_url_template,
        "localizations": localization_options(profile),
    }


def territory_payload(conn: sqlite3.Connection | None = None) -> dict:
    warehouse: dict | None = None
    warehouse_tid: str | None = None
    if conn is not None:
        warehouse = load_territory_config(conn)
        if warehouse:
            warehouse_tid = str(warehouse.get("territory_id") or "")

    admin = load_localization_admin()
    admin_tid: str | None = None
    try:
        admin_tid = admin.normalized_territory_id() if admin.territory_id else None
    except ValueError:
        admin_tid = None

    effective_tid = admin_tid or warehouse_tid or resolve_territory_id()
    profile = get_territory(effective_tid)
    payload = _profile_payload(profile, warehouse=warehouse)

    if warehouse and warehouse.get("updated_at"):
        payload["updated_at"] = warehouse["updated_at"]
    else:
        payload["updated_at"] = None

    payload["warehouse_territory_id"] = warehouse_tid
    if warehouse and warehouse.get("seed_language"):
        payload["seed_language"] = warehouse["seed_language"]
    else:
        payload["seed_language"] = profile.default_seed_language
    payload["admin_territory_id"] = admin.territory_id
    payload["territory_mismatch"] = bool(
        warehouse_tid and admin_tid and warehouse_tid != admin_tid
    )

    supported = resolve_supported_ui_locales(admin)
    preferred_ui: str | None = None
    if admin.ui_locale:
        try:
            preferred_ui = admin.normalized_ui_locale(territory_id=effective_tid)
        except ValueError:
            preferred_ui = None
    if preferred_ui and preferred_ui not in supported:
        preferred_ui = None
    payload["preferred_ui_locale"] = preferred_ui
    payload["supported_ui_locales"] = supported

    if not warehouse:
        base = default_territory_payload()
        for key in ("updated_at",):
            if key not in payload or payload[key] is None:
                payload[key] = base.get(key)

    return payload


def llm_market_context(conn: sqlite3.Connection | None = None) -> str:
    return str(territory_payload(conn).get("llm_market_context") or "")
