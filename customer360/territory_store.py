"""Persist and load territory configuration in the warehouse SQLite DB."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from customer360.territory import TerritoryProfile, get_territory, localization_options
from customer360.territory.languages import UI_LANGUAGE_IDS, resolve_seed_language

TERRITORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS APP_TERRITORY_CONFIG (
    TERRITORY_ID            TEXT NOT NULL PRIMARY KEY,
    DISPLAY_NAME            TEXT NOT NULL,
    CURRENCY                TEXT NOT NULL,
    INTL_LOCALE             TEXT NOT NULL,
    PRIMARY_UI_LOCALE       TEXT NOT NULL,
    SUPPORTED_UI_LOCALES    TEXT NOT NULL,
    CITY_NAMES_JSON         TEXT NOT NULL,
    LLM_MARKET_CONTEXT      TEXT NOT NULL,
    PORTAL_SMS_URL_TEMPLATE TEXT NOT NULL,
    SEED_LANGUAGE           TEXT,
    CITY_ALIASES_JSON       TEXT,
    SEED_MATERIAL_SOURCE    TEXT,
    UPDATED_AT              TEXT NOT NULL
);
"""


def ensure_territory_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(TERRITORY_SCHEMA)
    cols = {
        row[1]
        for row in conn.execute("PRAGMA table_info(APP_TERRITORY_CONFIG)").fetchall()
    }
    if "SEED_LANGUAGE" not in cols:
        conn.execute("ALTER TABLE APP_TERRITORY_CONFIG ADD COLUMN SEED_LANGUAGE TEXT")
    if "CITY_ALIASES_JSON" not in cols:
        conn.execute("ALTER TABLE APP_TERRITORY_CONFIG ADD COLUMN CITY_ALIASES_JSON TEXT")
    if "SEED_MATERIAL_SOURCE" not in cols:
        conn.execute("ALTER TABLE APP_TERRITORY_CONFIG ADD COLUMN SEED_MATERIAL_SOURCE TEXT")


def _aliases_from_city_names(city_names: list[str]) -> dict[str, str]:
    return {name.lower(): name for name in city_names if name}


def write_territory_config(
    conn: sqlite3.Connection,
    profile: TerritoryProfile,
    *,
    seed_language: str,
    city_names: list[str] | None = None,
    city_aliases: dict[str, str] | None = None,
    seed_material_source: str | None = None,
) -> None:
    ensure_territory_schema(conn)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    lang = resolve_seed_language(seed_language=seed_language, territory_id=profile.id)
    cities = city_names if city_names is not None else list(profile.canonical_cities())
    aliases = dict(city_aliases) if city_aliases is not None else profile.known_cities_map()
    for name in cities:
        aliases.setdefault(name.lower(), name)
    conn.execute(
        """
        INSERT INTO APP_TERRITORY_CONFIG (
            TERRITORY_ID, DISPLAY_NAME, CURRENCY, INTL_LOCALE, PRIMARY_UI_LOCALE,
            SUPPORTED_UI_LOCALES, CITY_NAMES_JSON, LLM_MARKET_CONTEXT,
            PORTAL_SMS_URL_TEMPLATE, SEED_LANGUAGE, CITY_ALIASES_JSON,
            SEED_MATERIAL_SOURCE, UPDATED_AT
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(TERRITORY_ID) DO UPDATE SET
            DISPLAY_NAME = excluded.DISPLAY_NAME,
            CURRENCY = excluded.CURRENCY,
            INTL_LOCALE = excluded.INTL_LOCALE,
            PRIMARY_UI_LOCALE = excluded.PRIMARY_UI_LOCALE,
            SUPPORTED_UI_LOCALES = excluded.SUPPORTED_UI_LOCALES,
            CITY_NAMES_JSON = excluded.CITY_NAMES_JSON,
            LLM_MARKET_CONTEXT = excluded.LLM_MARKET_CONTEXT,
            PORTAL_SMS_URL_TEMPLATE = excluded.PORTAL_SMS_URL_TEMPLATE,
            SEED_LANGUAGE = excluded.SEED_LANGUAGE,
            CITY_ALIASES_JSON = excluded.CITY_ALIASES_JSON,
            SEED_MATERIAL_SOURCE = excluded.SEED_MATERIAL_SOURCE,
            UPDATED_AT = excluded.UPDATED_AT
        """,
        (
            profile.id,
            profile.display_name,
            profile.default_currency,
            profile.default_intl_locale,
            profile.primary_ui_locale,
            json.dumps(list(UI_LANGUAGE_IDS)),
            json.dumps(cities),
            profile.llm_market_context,
            profile.portal_sms_url_template,
            lang,
            json.dumps(aliases),
            seed_material_source,
            now,
        ),
    )


def load_territory_config(conn: sqlite3.Connection) -> dict | None:
    ensure_territory_schema(conn)
    row = conn.execute(
        """
        SELECT TERRITORY_ID, DISPLAY_NAME, CURRENCY, INTL_LOCALE, PRIMARY_UI_LOCALE,
               SUPPORTED_UI_LOCALES, CITY_NAMES_JSON, LLM_MARKET_CONTEXT,
               PORTAL_SMS_URL_TEMPLATE, SEED_LANGUAGE, CITY_ALIASES_JSON,
               SEED_MATERIAL_SOURCE, UPDATED_AT
        FROM APP_TERRITORY_CONFIG
        ORDER BY UPDATED_AT DESC
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        return None
    keys = row.keys() if hasattr(row, "keys") else []
    get = row.__getitem__

    def _col(name: str, idx: int) -> str:
        if keys and name in keys:
            val = row[name]
            return "" if val is None else str(val)
        val = get(idx)
        return "" if val is None else str(val)

    cities = json.loads(_col("CITY_NAMES_JSON", 6))
    locales = json.loads(_col("SUPPORTED_UI_LOCALES", 5))
    territory_id = _col("TERRITORY_ID", 0)
    profile = get_territory(territory_id)
    seed_language = _col("SEED_LANGUAGE", 9) or profile.default_seed_language
    aliases_raw = _col("CITY_ALIASES_JSON", 10)
    if aliases_raw:
        city_aliases = json.loads(aliases_raw)
    else:
        city_aliases = _aliases_from_city_names(cities)
        city_aliases.update(profile.known_cities_map())
    return {
        "territory_id": territory_id,
        "display_name": _col("DISPLAY_NAME", 1),
        "currency": _col("CURRENCY", 2),
        "intl_locale": _col("INTL_LOCALE", 3),
        "primary_ui_locale": _col("PRIMARY_UI_LOCALE", 4),
        "supported_ui_locales": locales,
        "seed_language": seed_language,
        "seed_material_source": _col("SEED_MATERIAL_SOURCE", 11) or None,
        "cities": cities,
        "city_aliases": city_aliases,
        "llm_market_context": _col("LLM_MARKET_CONTEXT", 7),
        "portal_sms_url_template": _col("PORTAL_SMS_URL_TEMPLATE", 8),
        "updated_at": _col("UPDATED_AT", 12),
        "localizations": localization_options(profile),
    }


def default_territory_payload() -> dict:
    from customer360.territory.registry import DEFAULT_TERRITORY_ID

    profile = get_territory(DEFAULT_TERRITORY_ID)
    return {
        "territory_id": profile.id,
        "display_name": profile.display_name,
        "currency": profile.default_currency,
        "intl_locale": profile.default_intl_locale,
        "primary_ui_locale": profile.primary_ui_locale,
        "supported_ui_locales": list(UI_LANGUAGE_IDS),
        "seed_language": profile.default_seed_language,
        "cities": list(profile.canonical_cities()),
        "city_aliases": profile.known_cities_map(),
        "llm_market_context": profile.llm_market_context,
        "portal_sms_url_template": profile.portal_sms_url_template,
        "updated_at": None,
        "localizations": localization_options(profile),
    }
